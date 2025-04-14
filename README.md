# Spanish Teacher

A web-based application that helps users practice Spanish conversation skills through interactive audio dialogues with an AI assistant.

## Features

- **Interactive Conversations**: Engage in natural Spanish conversations with an AI assistant
- **Multiple Scenarios**: Practice in various contexts like restaurants, travel, shopping, and daily life
- **Difficulty Levels**: Choose between beginner, intermediate, and advanced levels
- **Voice Recognition**: Speak Spanish and get real-time feedback
- **Text-to-Speech**: Hear the AI's responses pronounced correctly
- **Learning Hints**: Get optional hints to help you understand and respond appropriately
- **Dual Processing Modes**: Choose between Gemini-only or Deepgram+Gemini for speech recognition

## Getting Started

### Prerequisites

- Python 3.8+
- Flask
- Google Cloud API credentials (for Gemini AI and Text-to-Speech)
- Deepgram API key (optional, for enhanced speech recognition)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/spanish-teacher.git
   cd spanish-teacher
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   DEEPGRAM_API_KEY=your_deepgram_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Open your browser and navigate to `http://localhost:5000`

## Usage

1. **Select Your Level**: Choose between beginner, intermediate, or advanced
2. **Choose a Scenario**: Select from options like restaurant, travel, shopping, etc.
3. **Pick a Topic**: Select a specific topic within the chosen scenario
4. **Start Conversation**: Begin the dialogue with the AI assistant
5. **Speak Spanish**: Use the recording button to capture your Spanish responses
6. **Get Feedback**: Receive corrections and suggestions from the AI
7. **Use Hints**: Toggle the "Need Hints" option if you need additional help

## Project Structure

- `app.py`: Main Flask application
- `conversation_manager.py`: Handles the conversation logic and AI interactions
- `config.py`: Configuration settings for scenarios and topics
- `templates/`: HTML templates for the web interface

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **AI**: Google Gemini API
- **Speech Recognition**: Deepgram API and Web Speech API
- **Text-to-Speech**:Open AI transcribe

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini API for powering the AI conversations
- Deepgram for speech recognition capabilities
- All contributors who have helped improve this project
