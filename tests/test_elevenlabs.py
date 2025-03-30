import os
from elevenlabs import generate, play, set_api_key, save
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Get API key from environment variable
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")

def text_to_speech(text, voice_id="pNInz6obpgDQGcFmaJgB", output_file=None):
    """
    Convert text to speech using ElevenLabs API.
    
    Args:
        text (str): Text to convert to speech
        voice_id (str): Voice ID to use (default: "pNInz6obpgDQGcFmaJgB" - Antoni, Spanish male voice)
        output_file (str): Path to save the audio file (optional)
    """
    try:
        # Set the API key
        set_api_key(ELEVEN_LABS_API_KEY)
        
        # Initialize the ElevenLabs client
        client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)
        
        print(f"Converting text to speech...")
        print(f"Text: {text}")
        print(f"Voice ID: {voice_id}")
        
        # Generate audio from text
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
        )
        
        # Save the audio file if output_file is provided
        if output_file:
            with open(output_file, 'wb') as f:
                f.write(audio)
            print(f"Audio saved to: {output_file}")
        
        # Play the audio
        print("Playing audio...")
        play(audio)
        
        # If we're playing the audio, wait a bit before returning
        time.sleep(2)
        
        return audio
        
    except Exception as e:
        print(f"Error during text-to-speech conversion: {str(e)}")
        return None

def main():
    # Get text from user
    text = input("Enter Spanish text to convert to speech: ")
    
    # Ask if user wants to save the audio
    save_option = input("Do you want to save the audio? (y/n): ").lower()
    
    output_file = None
    if save_option == 'y':
        output_file = input("Enter the output file path (e.g., output.mp3): ")
    
    # Convert text to speech
    text_to_speech(text, output_file=output_file)

if __name__ == "__main__":
    main() 