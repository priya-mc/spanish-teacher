import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "9a30a3ba85e47d6cfd4ad330f784b1769a6da0d4")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# LLM Configuration
LLM_MODEL = "gemini/gemini-2.0-flash"  # Base model for conversations
LLM_MODEL_FAST = "gemini/gemini-2.0-flash-lite"  # Faster model for quick responses
LLM_MODEL_AUDIO = "gemini-2.0-flash"

# MediaRecorder Configuration
MEDIA_RECORDER_TIMESLICE = 250  # milliseconds

# Deepgram Features
LANGUAGE = "es-419"  # Spanish (Latin America)
MODEL = "nova-2"
SMART_FORMAT = True
PUNCTUATE = True
DIARIZE = False

# Spanish Learning Levels
SPANISH_LEVELS = {
    "beginner": {
        "system_prompt": """You are a patient Spanish teacher named Elena for beginners. Follow these rules:
        1. Use basic vocabulary 
        2. DO NOT provide english translations of everything. Rarel you can do this for very complex words.
        3. Correct any mistakes gently
        4. Respond as a continuous sentence without line breaks. Always continue the conversation forward in Spanish, expressing your thoughts and asking questions.""",
        "max_complexity": 1
    },
    "intermediate": {
        "system_prompt": """You are a Spanish teacher named Elena for intermediate students. Follow these rules:
        1. Use moderate vocabulary and varied tenses
        2. Provide English translations only when needed
        3. Correct mistakes and explain grammar points
        4. Encourage more complex responses
        5. Use common idioms and explain them
        6. Balance challenge and support""",
        "max_complexity": 2
    },
    "advanced": {
        "system_prompt": """You are a Spanish conversation partner named Elena for advanced students. Follow these rules:
        1. Use natural, native-level Spanish
        2. Only translate complex or regional terms
        3. Focus on fluency and expression
        4. Discuss complex topics
        5. Use and explain colloquialisms
        6. Challenge the student to improve""",
        "max_complexity": 3
    }
}

# Conversation Scenarios
SPANISH_SCENARIOS = {
    "daily_life": {
        "name": "Daily Life and Routines",
        "topics": ["morning routine", "shopping", "dining out", "hobbies", "weather", "family"],
        "context": "Practice everyday conversations and common situations"
    },
    "travel": {
        "name": "Travel and Tourism",
        "topics": ["directions", "hotels", "transportation", "sightseeing", "cultural events", "emergencies"],
        "context": "Learn to navigate travel situations and cultural experiences"
    },
    "professional": {
        "name": "Professional Environment",
        "topics": ["job interview", "office communication", "presentations", "emails", "negotiations", "meetings"],
        "context": "Develop business Spanish skills and professional communication"
    }
}

# Helper Prompts
CORRECTION_PROMPT = """Analyze the student's response:
1. Identify any grammar mistakes. Avoid mistakes in written text or spellings since this is a voice conversation.
2. Provide corrections with explanations
3. Suggest alternative expressions
4. Maintain conversation flow"""

HINT_GENERATION_PROMPT = """Generate 1-2 helpful hints:
1. A simpler way to express the idea while speaking
2. A more complex alternative
3. A useful vocabulary suggestion
Make sure hints match the student's level: {level}"""


AUDIO_GENERATION_PROMPT = """Generate a response to the user message. Look at the conversation history to understand the context and the user's level.
In your output, give me the response as a continuous sentence without line breaks. Use the same language as the user message. Also give me a transcription of the user message.
JSON format:
{
    "response": "response to the user message",
    "transcription": "transcription of the user message"
}
"""