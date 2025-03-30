import asyncio
from conversation_manager import SpanishTeacher
import uuid

async def main():
    # Initialize the Spanish teacher
    teacher = SpanishTeacher()
    
    # Create a test user ID
    user_id = str(uuid.uuid4())
    
    try:
        # Start a session
        print("\n=== Starting Spanish Learning Session ===")
        session = await teacher.start_session(
            user_id=user_id,
            level="beginner",  # Options: beginner, intermediate, advanced
            scenario="daily_life"  # Options: daily_life, travel, professional
        )
        print("\nTeacher:", session['response'])

        # Example interaction
        while True:
            # Get user input
            user_input = input("\nYou (type 'quit' to exit, 'help' for hints): ")
            
            if user_input.lower() == 'quit':
                break
                
            need_help = user_input.lower() == 'help'
            if need_help:
                user_input = input("\nWhat would you like to say? ")

            # Process message
            response = await teacher.process_message(
                user_id=user_id,
                message=user_input,
                need_help=need_help
            )
            
            print("\nTeacher:", response['response'])
            
            if response.get('hints'):
                print("\nHints:")
                for hint in response['hints']:
                    print(f"- {hint}")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Clear the session
        teacher.clear_session(user_id)

if __name__ == "__main__":
    asyncio.run(main()) 