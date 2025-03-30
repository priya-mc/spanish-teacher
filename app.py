from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from elevenlabs.client import ElevenLabs
from loguru import logger
import os
import json
import asyncio
import threading
import time
from functools import wraps
import uuid
from werkzeug.utils import secure_filename
from typing import Optional, Dict, Any
from prometheus_client import Counter, Histogram, generate_latest
from config import *
from dotenv import load_dotenv

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')  # Use threading mode

# Configure logging
logger.add("app.log", rotation="500 MB", retention="10 days", level="INFO")

# Load environment variables
load_dotenv()

# Initialize Deepgram and Eleven Labs
dg_client = DeepgramClient(DEEPGRAM_API_KEY)
eleven_labs_client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)

# Configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store Deepgram connections for each client
deepgram_connections = {}
# Store locks for each client
client_locks = {}
# Store exit flags for each client
client_exits = {}

# Add metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])

# Request tracking middleware
@app.before_request
def before_request():
    request.id = str(uuid.uuid4())
    request.start_time = time.time()
    logger.info(f"Request {request.id}: {request.method} {request.path}")

# Error handler
@app.errorhandler(Exception)
def handle_error(error):
    logger.exception(f"Request {getattr(request, 'id', 'unknown')} failed")
    return jsonify({
        "error": str(error),
        "request_id": getattr(request, 'id', 'unknown')
    }), 500

# Rate limiting decorator
def rate_limit(calls: int, period: float):
    def decorator(f):
        last_reset = time.time()
        calls_made = 0

        @wraps(f)
        def wrapper(*args, **kwargs):
            nonlocal last_reset, calls_made
            now = time.time()
            
            if now - last_reset > period:
                calls_made = 0
                last_reset = now
            
            if calls_made >= calls:
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            calls_made += 1
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Utility functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": time.time()})

# Speech-to-Text streaming endpoint (Deepgram)
@app.route('/api/v1/stt/stream', methods=['POST'])
@rate_limit(calls=100, period=3600)
async def stream_stt():
    try:
        if 'audio' not in request.files:
            raise ValueError("No audio file provided")

        file = request.files['audio']
        if not allowed_file(file.filename):
            raise ValueError("Invalid file type")

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        async def generate():
            try:
                source = {'buffer': open(filepath, 'rb'), 'mimetype': 'audio/wav'}
                options = {
                    'punctuate': True,
                    'model': STT_MODEL,
                    'language': STT_LANGUAGE,
                    'encoding': 'linear16',
                    'channels': 1,
                    'sample_rate': 16000
                }

                response = await dg_client.transcription.live.v("1").listen(source, options)
                
                async for result in response:
                    if result.is_final:
                        yield f"data: {json.dumps(result.channel.alternatives[0].transcript)}\n\n"

            except Exception as e:
                logger.exception("Streaming STT error")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            finally:
                os.remove(filepath)  # Clean up temporary file

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        logger.exception("STT endpoint error")
        return jsonify({"error": str(e)}), 400

# Text-to-Speech streaming endpoint (Eleven Labs)
@app.route('/api/v1/tts/stream', methods=['POST'])
@rate_limit(calls=100, period=3600)
async def stream_tts():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            raise ValueError("No text provided")

        text = data['text']
        voice_id = data.get('voice', DEFAULT_VOICE_ID)
        model = data.get('model', TTS_MODEL)

        def generate_audio():
            try:
                # Use the new client API
                audio = eleven_labs_client.text_to_speech.convert(
                    text=text,
                    voice_id=voice_id,
                    model_id=model,
                    output_format="mp3_44100_128",
                )
                
                # Return the audio as a single chunk since the new API doesn't stream by default
                yield audio

            except Exception as e:
                logger.exception("Streaming TTS error")
                yield b''

        return Response(
            generate_audio(),
            mimetype='audio/mpeg',
            headers={
                'X-Content-Type-Options': 'nosniff',
                'Content-Disposition': 'attachment; filename=speech.mp3'
            }
        )

    except Exception as e:
        logger.exception("TTS endpoint error")
        return jsonify({"error": str(e)}), 400

@socketio.on('connect', namespace='/api/v1/stt/websocket')
def stt_connect():
    logger.info(f"Client connected to STT WebSocket: {request.sid}")
    emit('connect_response', {"status": "Connected"})

@socketio.on('disconnect', namespace='/api/v1/stt/websocket')
def stt_disconnect():
    # Capture the session ID
    session_id = request.sid
    logger.info(f"Client disconnected from STT WebSocket: {session_id}")
    
    # Clean up any resources
    if session_id in deepgram_connections:
        try:
            # Signal the thread to exit
            if session_id in client_locks and session_id in client_exits:
                with client_locks[session_id]:
                    client_exits[session_id] = True
            
            # Close the Deepgram connection
            deepgram_connections[session_id].finish()
            del deepgram_connections[session_id]
            
            # Clean up locks and exit flags
            if session_id in client_locks:
                del client_locks[session_id]
            if session_id in client_exits:
                del client_exits[session_id]
                
            logger.info(f"Cleaned up Deepgram connection for {session_id}")
        except Exception as e:
            logger.exception(f"Error cleaning up for {session_id}")

@socketio.on('start', namespace='/api/v1/stt/websocket')
def stt_start(data):
    try:
        # Capture the session ID before starting the thread
        session_id = request.sid
        logger.info(f"Starting STT session for {session_id} with data: {data}")
        
        # Setup Deepgram connection options
        options = LiveOptions(
            model=STT_MODEL,
            language=STT_LANGUAGE,
            punctuate=True,
            encoding="linear16",
            channels=data.get('channels', 1),
            sample_rate=data.get('sample_rate', 16000),
            interim_results=True
        )
        
        logger.info(f"Creating Deepgram connection with options: {options}")
        
        # Create a new Deepgram connection
        dg_connection = dg_client.listen.websocket.v("1")
        
        # Initialize lock and exit flag for this client
        client_locks[session_id] = threading.Lock()
        client_exits[session_id] = False
        
        # Define the transcript callback
        def on_message(self, result, **kwargs):
            try:
                logger.info(f"Received result from Deepgram: {result}")
                
                if hasattr(result, 'is_final'):
                    is_final = result.is_final
                else:
                    is_final = True  # Assume final if not specified
                    
                logger.info(f"Result is_final: {is_final}")
                
                if is_final:
                    if hasattr(result, 'channel') and hasattr(result.channel, 'alternatives') and len(result.channel.alternatives) > 0:
                        transcript = result.channel.alternatives[0].transcript
                        confidence = getattr(result.channel.alternatives[0], 'confidence', 0.0)
                        
                        logger.info(f"Extracted transcript: '{transcript}' with confidence: {confidence}")
                        
                        if len(transcript.strip()) > 0:
                            logger.info(f"Emitting transcript for {session_id}: {transcript}")
                            socketio.emit('transcript', {
                                "transcript": transcript,
                                "confidence": confidence
                            }, namespace='/api/v1/stt/websocket', room=session_id)
                        else:
                            logger.info(f"Empty transcript received, not emitting")
                    else:
                        logger.warning(f"Result does not have expected structure: {result}")
                else:
                    logger.debug(f"Received non-final result, ignoring")
            except Exception as e:
                logger.exception(f"Error in transcript callback for {session_id}")
                socketio.emit('error', {"error": str(e)}, namespace='/api/v1/stt/websocket', room=session_id)
        
        # Register the callback
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        
        # Start the connection
        if dg_connection.start(options) is False:
            logger.error(f"Failed to start Deepgram connection for {session_id}")
            emit('error', {"error": "Failed to start Deepgram connection"}, namespace='/api/v1/stt/websocket')
            return
        
        # Store the connection
        deepgram_connections[session_id] = dg_connection
        
        # Emit ready event
        emit('ready', {"status": "Listening"}, namespace='/api/v1/stt/websocket')
        
        logger.info(f"Deepgram connection started for {session_id}")
    
    except Exception as e:
        logger.exception(f"Error starting STT session for {session_id}")
        emit('error', {"error": str(e)}, namespace='/api/v1/stt/websocket')

@socketio.on('audio', namespace='/api/v1/stt/websocket')
def stt_audio(audio_data):
    try:
        # Capture the session ID
        session_id = request.sid
        
        if session_id in deepgram_connections:
            # Check if we should exit
            if session_id in client_locks and session_id in client_exits:
                with client_locks[session_id]:
                    if client_exits[session_id]:
                        logger.info(f"Skipping audio processing for {session_id} as exit is flagged")
                        return
            
            # Log audio data size
            data_size = len(audio_data) if audio_data else 0
            logger.debug(f"Received audio data from {session_id}: {data_size} bytes")
            
            # Send audio data to Deepgram
            deepgram_connections[session_id].send(audio_data)
        else:
            logger.warning(f"No active Deepgram connection for {session_id}")
            emit('error', {"error": "No active Deepgram connection"}, namespace='/api/v1/stt/websocket')
    
    except Exception as e:
        logger.exception(f"Error processing audio for {session_id}")
        emit('error', {"error": str(e)}, namespace='/api/v1/stt/websocket')

@socketio.on('stop', namespace='/api/v1/stt/websocket')
def stt_stop():
    try:
        # Capture the session ID
        session_id = request.sid
        logger.info(f"Stopping STT session for {session_id}")
        
        if session_id in deepgram_connections:
            # Signal the thread to exit
            if session_id in client_locks and session_id in client_exits:
                with client_locks[session_id]:
                    client_exits[session_id] = True
            
            # Close the Deepgram connection
            deepgram_connections[session_id].finish()
            
            # Clean up
            del deepgram_connections[session_id]
            if session_id in client_locks:
                del client_locks[session_id]
            if session_id in client_exits:
                del client_exits[session_id]
            
            logger.info(f"Closed Deepgram connection for {session_id}")
            emit('stopped', {"status": "Stopped"}, namespace='/api/v1/stt/websocket')
        else:
            logger.warning(f"No active Deepgram connection for {session_id}")
            emit('error', {"error": "No active Deepgram connection"}, namespace='/api/v1/stt/websocket')
    
    except Exception as e:
        logger.exception(f"Error stopping STT session for {session_id}")
        emit('error', {"error": str(e)}, namespace='/api/v1/stt/websocket')

# Add metrics endpoint
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

# Add after_request handler
@app.after_request
def after_request(response):
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()
    
    if hasattr(request, 'start_time'):
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.path
        ).observe(time.time() - request.start_time)
    
    return response

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    # Use socketio.run instead of app.run, but with the correct parameters
    socketio.run(app, host='0.0.0.0', port=5000, debug=os.getenv('FLASK_ENV') == 'development', allow_unsafe_werkzeug=True) 