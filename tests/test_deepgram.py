import os
import json
import argparse
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)
import dotenv

dotenv.load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

def transcribe_audio(audio_file_path, language="es"):
    """
    Transcribe an audio file using Deepgram.
    
    Args:
        audio_file_path (str): Path to the audio file
        language (str): Language code (default: "es" for Spanish)
    """
    try:
        # Check if file exists
        if not os.path.exists(audio_file_path):
            print(f"Error: File not found: {audio_file_path}")
            return
        
        # STEP 1: Create a Deepgram client
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        
        # Read the audio file
        with open(audio_file_path, "rb") as file:
            buffer_data = file.read()
        
        payload: FileSource = {
            "buffer": buffer_data,
        }
        
        # STEP 2: Configure Deepgram options for audio analysis
        options = PrerecordedOptions(
            model="nova-2",
            language="multi",
            smart_format=True,
        )
        
        # Send the audio to Deepgram for transcription
        print(f"Transcribing file: {audio_file_path}")
        print(f"Language detection: Enabled (multi)")
        print("Processing...")
        
        # STEP 3: Call the transcribe_file method with the payload and options
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
        
        # STEP 4: Extract and print the transcript and language information
        print("\nTranscription Results:")
        print("-" * 50)
        
        # Extract transcript from the response
        transcript = response.results.channels[0].alternatives[0].transcript
        confidence = response.results.channels[0].alternatives[0].confidence
        
        # Print the transcript
        print(f"Transcript: {transcript}")
        print(f"Confidence: {confidence:.2f}")
        
        # Extract language information if available
        if hasattr(response.results.channels[0].alternatives[0], 'languages'):
            languages = response.results.channels[0].alternatives[0].languages
            print(f"Detected Languages: {', '.join(languages)}")
        
        print("-" * 50)
        
        # STEP 5: Write the full JSON response to a file
        # Create output filename based on input filename
        base_name = os.path.splitext(os.path.basename(audio_file_path))[0]
        output_file = f"{base_name}_transcription.json"
        
        # Write JSON to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.to_json(indent=4))
        
        print(f"Full JSON response written to: {output_file}")
        
        return transcript
            
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Transcribe audio files using Deepgram with language detection.')
    parser.add_argument('--file', '-f', type=str, help='Path to the audio file to transcribe')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Get audio file path from arguments or prompt user if not provided
    audio_file = args.file
    if not audio_file:
        audio_file = input("Enter the path to your audio file: ")
    
    # Run the transcription function with multi-language detection
    transcribe_audio(audio_file)

if __name__ == "__main__":
    main() 