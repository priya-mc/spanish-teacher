from litellm import completion
from loguru import logger
from typing import Dict, List, Optional
from config import (
    LLM_MODEL, LLM_MODEL_FAST, GEMINI_API_KEY,
    SPANISH_LEVELS, SPANISH_SCENARIOS,
    CORRECTION_PROMPT, HINT_GENERATION_PROMPT
)

class SpanishTeacher:
    def __init__(self):
        self.conversations: Dict[str, List[Dict]] = {}
        self.user_levels: Dict[str, str] = {}
        self.user_scenarios: Dict[str, str] = {}

    async def start_session(self, user_id: str, level: str, scenario: str) -> Dict:
        """Initialize or reset a learning session for a user"""
        try:
            if level not in SPANISH_LEVELS or scenario not in SPANISH_SCENARIOS:
                raise ValueError("Invalid level or scenario")

            self.user_levels[user_id] = level
            self.user_scenarios[user_id] = scenario
            
            # Initialize conversation with system prompt
            self.conversations[user_id] = [{
                "role": "system",
                "content": SPANISH_LEVELS[level]["system_prompt"]
            }]

            # Generate initial conversation starter
            scenario_info = SPANISH_SCENARIOS[scenario]
            starter_prompt = f"""Start a conversation about {scenario_info['name']}.
            Topic: {scenario_info['topics'][0]}
            Context: {scenario_info['context']}
            Remember to follow the teaching style for {level} level."""

            response = completion(
                model=LLM_MODEL,
                messages=self.conversations[user_id] + [{"role": "user", "content": starter_prompt}],
                api_key=GEMINI_API_KEY
            )

            starter_message = response.choices[0].message.content
            self.conversations[user_id].append({"role": "assistant", "content": starter_message})

            return {
                "response": starter_message,
                "scenario": scenario_info,
                "level": level
            }

        except Exception as e:
            logger.exception(f"Error starting session for user {user_id}")
            raise

    async def process_message(self, user_id: str, message: str, need_help: bool = False) -> Dict:
        """Process a student's message and provide appropriate response"""
        try:
            if user_id not in self.conversations:
                raise ValueError("No active session found")

            level = self.user_levels[user_id]
            
            # Add user message to history
            self.conversations[user_id].append({"role": "user", "content": message})

            # Generate response
            prompt = CORRECTION_PROMPT if need_help else f"Respond as a Spanish teacher for {level} level"
            
            response = completion(
                model=LLM_MODEL,
                messages=self.conversations[user_id] + [{"role": "user", "content": prompt}],
                api_key=GEMINI_API_KEY
            )

            assistant_message = response.choices[0].message.content
            self.conversations[user_id].append({"role": "assistant", "content": assistant_message})

            # Generate hints if needed
            hints = None
            if need_help:
                hints = await self._generate_hints(user_id)

            return {
                "response": assistant_message,
                "hints": hints,
                "level": level
            }

        except Exception as e:
            logger.exception(f"Error processing message for user {user_id}")
            raise

    async def _generate_hints(self, user_id: str) -> List[str]:
        """Generate helpful hints for the student"""
        try:
            level = self.user_levels[user_id]
            prompt = HINT_GENERATION_PROMPT.format(level=level)

            response = completion(
                model=LLM_MODEL_FAST,
                messages=[{"role": "user", "content": prompt}],
                api_key=GEMINI_API_KEY
            )

            return response.choices[0].message.content.split('\n')

        except Exception as e:
            logger.exception(f"Error generating hints for user {user_id}")
            return ["Lo siento, I couldn't generate hints right now."]

    def get_conversation_history(self, user_id: str) -> Optional[List[Dict]]:
        """Retrieve conversation history for a user"""
        return self.conversations.get(user_id, None)

    def clear_session(self, user_id: str) -> None:
        """Clear a user's session data"""
        self.conversations.pop(user_id, None)
        self.user_levels.pop(user_id, None)
        self.user_scenarios.pop(user_id, None) 