import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# LLM Configuration
LLM_MODEL = "gemini/gemini-2.0-flash"  # Base model for conversations
LLM_MODEL_FAST = "gemini/gemini-2.0-flash-lite"  # Faster model for quick responses

# Spanish Learning Levels
SPANISH_LEVELS = {
    "beginner": {
        "system_prompt": """You are a patient Spanish teacher for beginners. Follow these rules:
        1. Use basic vocabulary and simple present tense
        2. Speak slowly and clearly
        3. Always provide English translations
        4. Correct any mistakes gently
        5. Give pronunciation tips
        6. Keep sentences short and simple""",
        "max_complexity": 1
    },
    "intermediate": {
        "system_prompt": """You are a Spanish teacher for intermediate students. Follow these rules:
        1. Use moderate vocabulary and varied tenses
        2. Provide English translations only when needed
        3. Correct mistakes and explain grammar points
        4. Encourage more complex responses
        5. Use common idioms and explain them
        6. Balance challenge and support""",
        "max_complexity": 2
    },
    "advanced": {
        "system_prompt": """You are a Spanish conversation partner for advanced students. Follow these rules:
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
1. Identify any grammar or vocabulary mistakes. Avoid mistakes in written text since this is a voice conversation.
2. Provide corrections with explanations
3. Suggest alternative expressions
4. Give positive reinforcement
5. Maintain conversation flow"""

HINT_GENERATION_PROMPT = """Generate three helpful hints:
1. A simpler way to express the idea
2. A more complex alternative
3. A useful vocabulary suggestion
Make sure hints match the student's level: {level}"""

# Speech Configuration
STT_MODEL = "nova-2"
STT_LANGUAGE = "es-419"
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"
TTS_MODEL = "eleven_monolingual_v1"

# API Configuration
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 