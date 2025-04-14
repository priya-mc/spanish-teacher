import json
from litellm import completion, create_file
from loguru import logger
from typing import Dict, List, Optional
from config import (
    LLM_MODEL, LLM_MODEL_FAST, LLM_MODEL_AUDIO, GEMINI_API_KEY,
    SPANISH_LEVELS, SPANISH_SCENARIOS,
    CORRECTION_PROMPT, HINT_GENERATION_PROMPT, AUDIO_GENERATION_PROMPT
)
from json_repair import repair_json
from datetime import datetime
import re
import logging
import os

from google import genai
from google.genai.types import GenerateContentConfig

generation_config = {
  "temperature":0.2,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 512,
  "response_mime_type": "application/json",
}

class SpanishTeacher:
    def __init__(self):
        self.conversations: Dict[str, List[Dict]] = {}
        self.user_levels: Dict[str, str] = {}
        self.user_scenarios: Dict[str, str] = {}
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    def get_logger(self, user_id):
        # Create a logger for each user
        logger = logging.getLogger(user_id)
        logger.setLevel(logging.INFO)
        
        # Create a file handler
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{user_id}_{timestamp}.log"
        log_path = os.path.join(log_dir, log_filename)
        
        # Check if the logger already has handlers
        if not logger.handlers:
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.INFO)
            
            # Create a logging format
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Add the handlers to the logger
            logger.addHandler(file_handler)
        
        return logger

    async def start_session(self, user_id: str, level: str, scenario: str, topic: str) -> Dict:
        """
        Start a new learning session with the specified level, scenario, and topic.
        
        Args:
            user_id (str): Unique identifier for the user
            level (str): Spanish proficiency level (beginner, intermediate, advanced)
            scenario (str): Conversation scenario key
            topic (str): Specific topic within the scenario
            
        Returns:
            dict: Initial response from the AI
        """
        # Validate inputs
        if level not in SPANISH_LEVELS:
            raise ValueError(f"Invalid level: {level}")
        
        if scenario not in SPANISH_SCENARIOS:
            raise ValueError(f"Invalid scenario: {scenario}")
        
        # Validate that the topic exists in the scenario
        if topic not in SPANISH_SCENARIOS[scenario]["topics"]:
            raise ValueError(f"Invalid topic '{topic}' for scenario '{scenario}'")
        
        # Get level and scenario details
        level_config = SPANISH_LEVELS[level]
        scenario_config = SPANISH_SCENARIOS[scenario]
        
        # Create system prompt
        system_prompt = f"""{level_config['system_prompt']}
        
        CONVERSATION CONTEXT:
        Scenario: {scenario_config['name']}
        Topic: {topic}
        Context: {scenario_config['context']}
        
        Start the conversation by introducing yourself as a Spanish teacher and begin a 
        conversation about {topic} within the context of {scenario_config['name']}.
        """
        
        # Initialize conversation history
        conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Hi!"}
        ]        
        # Store in user sessions
        self.user_levels[user_id] = level
        self.user_scenarios[user_id] = scenario
        self.conversations[user_id] = conversation_history
        
        # Generate response using LLM
        response = completion(
            model=LLM_MODEL,
            messages=conversation_history,
            api_key=GEMINI_API_KEY
        )
        
        # Extract the response text
        assistant_message = response.choices[0].message.content
        logger = self.get_logger(user_id)        
        
        # Add the response to conversation history
        self.conversations[user_id].append({"role": "assistant", "content": assistant_message})
        
        # Log the start of a session
        
        logger = self.get_logger(user_id)
        logger.info(f"Session started: Level={level}, Scenario={scenario}, Topic={topic}")
        
        # Log the initial message
        logger.info(f"System: {system_prompt}")
        logger.info(f"Assistant message: {assistant_message} at time: {datetime.now()}")
        
        ### Calculate token usage
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        return {"response": assistant_message}

    async def process_message(self, user_id: str, message: str, need_help: bool = False) -> dict:
        """
        Process a message from the student and generate a response.
        
        Args:
            user_id (str): Unique identifier for the user
            message (str): Message from the student
            need_help (bool): Whether the student is requesting help
            
        Returns:
            dict: Response from the AI, including hints if help was requested
        """
        try:
            if user_id not in self.conversations:
                raise ValueError("No active session found")
            
            # Log the user's message
            logger = self.get_logger(user_id)
            logger.info(f"User: {message}")
            
            # Add user message to conversation history
            self.conversations[user_id].append(
                {"role": "user", "content": message}
            )
            
            # If help is requested, generate hints
            hints = []
            if need_help:
                hints = await self._generate_hints(user_id, message)

            # Generate response
            response = await self._generate_response(user_id)
            
            # Log the AI's response
            logger.info(f"assistant message: {response}")
            
            ### Calculate token usage
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            
            # Return response with hints if requested
            return {
                "response": response,
                "hints": hints
            }
            
        except Exception as e:
            print(f"Error processing message for user {user_id}: {str(e)}")
            return {
                "response": "Lo siento, I'm having trouble responding right now. Please try again.",
                "hints": []
            }

    async def _generate_hints(self, user_id: str, message: str) -> list:
        """
        Generate helpful hints for the student based on their message.
        
        Args:
            user_id (str): Unique identifier for the user
            message (str): Message from the student
            
        Returns:
            list: List of hints
        """
        try:
            if user_id not in self.conversations:
                raise ValueError("No active session found")
            
            # Get user level
            level = self.user_levels[user_id]
            
            # Create prompt for hint generation
            hint_prompt = HINT_GENERATION_PROMPT.format(level=level)
            
            # Generate hints
            response = completion(
                model=LLM_MODEL_FAST,  # Use faster model for hints
                messages=[
                    {"role": "system", "content": hint_prompt},
                    {"role": "user", "content": message}
                ],
                api_key=GEMINI_API_KEY
            )
            
            # Extract hints
            hints_text = response.choices[0].message.content
            
            # Parse hints (assuming they're numbered or bulleted)
            hints = []
            for line in hints_text.strip().split('\n'):
                # Remove numbering or bullets and trim
                cleaned_line = re.sub(r'^\d+\.\s*|\*\s*', '', line).strip()
                if cleaned_line:
                    hints.append(cleaned_line)

            ### Add logging on hints
            logger.info(f"Hints: {hints}")
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            
            return hints
            
        except Exception as e:
            print(f"Error generating hints for user {user_id}: {str(e)}")
            return []

    async def _generate_response(self, user_id: str) -> str:
        """
        Generate a response from the AI based on the conversation history.
        
        Args:
            user_id (str): Unique identifier for the user
            
        Returns:
            str: Generated response from the AI
        """
        try:
            if user_id not in self.conversations:
                raise ValueError("No active session found")
            
            # Get conversation history
            conversation_history = self.conversations[user_id]
            
            # Generate response using LLM
            response = completion(
                model=LLM_MODEL,
                messages=conversation_history,
                api_key=GEMINI_API_KEY
            )
            
            # Extract the response text
            assistant_message = response.choices[0].message.content
            
            # Add the response to conversation history
            self.conversations[user_id].append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error generating response for user {user_id}: {str(e)}")
            return "Lo siento, I'm having trouble responding right now. Please try again."

    def get_conversation_history(self, user_id: str) -> Optional[List[Dict]]:
        """Retrieve conversation history for a user"""
        return self.conversations.get(user_id, None)

    def clear_session(self, user_id: str) -> None:
        """Clear a user's session data"""
        self.conversations.pop(user_id, None)
        self.user_levels.pop(user_id, None)
        self.user_scenarios.pop(user_id, None)

    async def process_audio_file(self, user_id: str, file_path: str, need_help: bool = False) -> dict:
        """
        Process an audio file using Gemini.
        
        Args:
            user_id (str): Unique identifier for the user
            file_path (str): Path to the audio file
            
        Returns:
            dict: Dictionary containing the transcript and AI response
        """
        try:
            if user_id not in self.conversations:
                raise ValueError("No active session found")
            
            ### Upload this file to Gemini
            client = genai.Client(api_key=GEMINI_API_KEY)
            myfile = client.files.upload(file=file_path)
            generation_config["system_instruction"] = AUDIO_GENERATION_PROMPT

            conversation = self.conversations[user_id]
            user_prompt = f"Here is the conversation history: {conversation} and the audio attached has the latest user message"

            llm_response = client.models.generate_content(
                model=LLM_MODEL_AUDIO,
                contents=[user_prompt, myfile],
                config=generation_config
            )
            
            ### Extract the response
            result= llm_response.text
            result = json.loads(repair_json(result))
            transcript = result["transcription"]
            response = result["response"]
            
            if not transcript:
                raise ValueError("Failed to transcribe audio")
            
            # Add user message to conversation history
            self.conversations[user_id].append({"role": "user", "content": transcript})
            self.conversations[user_id].append({"role": "assistant", "content": response})

            logger = self.get_logger(user_id)
            logger.info(f"User: {transcript}")
            logger.info(f"assistant message: {response}")

            ### Calculate token usage
            input_tokens = llm_response.usage_metadata.prompt_token_count
            output_tokens = llm_response.usage_metadata.candidates_token_count
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            
            # If help is requested, generate hints
            hints = []
            if need_help:
                hints = await self._generate_hints(user_id, transcript)
               

            ### Add logging on token usage
            logger.info(f"Total input tokens: {self.total_input_tokens}")
            logger.info(f"Total output tokens: {self.total_output_tokens}")
            
            return {
                "response": response,
                "hints": hints
            }
            
        except Exception as e:
            logger.error(f"Error processing audio file for user {user_id}: {str(e)}")
            return {
                "response": "Lo siento, I'm having trouble processing your audio. Please try again.",
                "hints": []
            }