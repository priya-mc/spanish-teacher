import os
import asyncio
from deepgram import DeepgramClient, PrerecordedOptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

async def transcribe_audio(audio_file_path, language="es"):
    """
    Transcribe an audio file using Deepgram.
    
    Args:
        audio_file_path (str): Path to the audio file
        language (str): Language code (default: "es" for Spanish)
    """
    try:
        # Initialize the Deepgram client
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        
        # Check if file exists
        if not os.path.exists(audio_file_path):
            print(f"Error: File not found: {audio_file_path}")
            return
        
        # Open the audio file
        with open(audio_file_path, "rb") as audio:
            # Set up options for transcription
            options = PrerecordedOptions(
                model="nova-2",
                language=language,
                smart_format=True,
                punctuate=True,
            )
            
            # Send the audio to Deepgram for transcription
            print(f"Transcribing file: {audio_file_path}")
            print(f"Language: {language}")
            print("Processing...")
            
            response = await deepgram.transcription.prerecorded.transcribe(audio, options)
            
            # Get the transcript from the response
            transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
            confidence = response["results"]["channels"][0]["alternatives"][0]["confidence"]
            
            print("\nTranscription Results:")
            print("-" * 50)
            print(f"Transcript: {transcript}")
            print(f"Confidence: {confidence:.2f}")
            print("-" * 50)
            
            return transcript
            
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        return None

def main():
    # Get audio file path from user
    audio_file = input("Enter the path to your Spanish audio file: ")
    
    # Run the async function
    asyncio.run(transcribe_audio(audio_file, "es"))

if __name__ == "__main__":
    main() 