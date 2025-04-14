import time
from flask import Flask, render_template, jsonify, request, session
from dotenv import load_dotenv
import os
import config
import uuid
from conversation_manager import SpanishTeacher
import asyncio
import tempfile
from openai import OpenAI
import io
import base64
import shutil
import subprocess

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Initialize Spanish Teacher
spanish_teacher = SpanishTeacher()

# Initialize OpenAI client (synchronous)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def index():
    # Generate a unique session ID if not present
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/api/get-config')
def get_config():
    """Return the configuration to the frontend"""
    return jsonify({
        "apiKey": config.DEEPGRAM_API_KEY,
        "language": config.LANGUAGE,
        "model": config.MODEL,
        "smartFormat": config.SMART_FORMAT,
        "punctuate": config.PUNCTUATE,
        "diarize": config.DIARIZE,
        "mediaRecorderTimeslice": config.MEDIA_RECORDER_TIMESLICE,
        "levels": list(config.SPANISH_LEVELS.keys()),
        "scenarios": {
            k: {
                "name": v["name"],
                "topics": v["topics"]  # Include the topics array for each scenario
            } 
            for k, v in config.SPANISH_SCENARIOS.items()
        }
    })

@app.route('/api/start-session', methods=['POST'])
def start_session():
    """Start a new learning session"""
    data = request.json
    user_id = session.get('user_id')
    level = data.get('level')
    scenario = data.get('scenario')
    topic = data.get('topic')  # Get the topic parameter

    print(f"Starting session with user_id: {user_id}, level: {level}, scenario: {scenario}, topic: {topic}")
    
    if not user_id or not level or not scenario or not topic:  # Add topic to validation
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        # Run the async function with the topic parameter
        result = asyncio.run(spanish_teacher.start_session(user_id, level, scenario, topic))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/process-message', methods=['POST'])
def process_message():
    """Process a student's message"""
    data = request.json
    user_id = session.get('user_id')
    message = data.get('message')
    need_help = data.get('needHelp', False)
    
    if not user_id or not message:
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        # Run the async function
        result = asyncio.run(spanish_teacher.process_message(user_id, message, need_help))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-history')
def get_history():
    """Get conversation history"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"error": "No active session"}), 400
    
    history = spanish_teacher.get_conversation_history(user_id)
    if not history:
        return jsonify({"error": "No conversation history found"}), 404
    
    return jsonify({"history": history})

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """Process an audio file using Gemini"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"error": "No active session"}), 400
    
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    need_help = request.form.get('needHelp', 'false').lower() == 'true'
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Save the original WebM file
        webm_path = os.path.join(temp_dir, 'audio.webm')
        audio_file.save(webm_path)
        
        # Convert WebM to WAV using FFmpeg
        wav_path = os.path.join(temp_dir, 'audio.wav')
        try:
            # Run FFmpeg to convert WebM to WAV
            subprocess.run(
                ['ffmpeg', '-i', webm_path, '-ar', '16000', '-ac', '1', wav_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Verify the WAV file was created
            if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                # Process the WAV file with Gemini
                result = asyncio.run(spanish_teacher.process_audio_file(user_id, wav_path, need_help))
                
                # Clean up
                shutil.rmtree(temp_dir)
                
                return jsonify(result)
            else:
                raise ValueError("WAV conversion failed: Output file is empty or not created")
                
        except subprocess.CalledProcessError as e:
            error_message = f"FFmpeg conversion error: {e.stderr.decode() if e.stderr else str(e)}"
            print(error_message)
            return jsonify({"error": error_message}), 500
            
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Clean up if temp_dir was created
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
            
        return jsonify({"error": str(e)}), 500

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech using OpenAI TTS"""
    data = request.json
    text = data.get('text')
    print(f"Text to speech: {text}")
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        # Generate speech using OpenAI
        response = openai_client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="echo",  # You can make this configurable
            input=text,
            instructions="You are a smart assistant that speaks spanish and english. Speak the spanish text as spanish should be spoken in a conversation and english as it should be spoken in a conversation with clear pronunciation.",
            response_format="mp3",
        )
        
        # Get the audio content directly
        # The response object should have the audio data directly accessible
        audio_data = response.content
        
        # Convert to base64 for sending to frontend
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return jsonify({
            "audio": audio_base64,
            "format": "mp3"
        })
        
    except Exception as e:
        print(f"TTS error: {str(e)}")
        import traceback
        traceback.print_exc()  # Print the full traceback for debugging
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
