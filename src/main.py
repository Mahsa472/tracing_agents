import sys
from pathlib import Path

# Ensure project root and src are on path so "schemas" and "tools"/"agents" resolve
_src = Path(__file__).resolve().parent
_root = _src.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from tools import get_weather, get_current_time
from agents import call_weather_time_agent


#Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_MODEL"] = os.getenv("OPENAI_MODEL")

# Initialize the model
model = ChatOpenAI(model=os.environ["OPENAI_MODEL"], temperature=0)

def main():
    try:
        print("=" * 60)
        print("Weather and Time Assistant")
        print("=" * 60)
        print("I can help you with:")
        print("  - Weather information for any city (use get_weather tool)")
        print("  - Current time for any city (use get_current_time tool)")
        print("\nType 'exit' or 'quit' to end the conversation.\n")

        print("Calling agent...")
        print("Agent ready! You can start asking questions.\n")
            
            # Conversation history
        conversation_history = []
        
        # Interactive loop
        while True:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
                print("\nGoodbye! Have a great day!")
                break
            
            if not user_input:
                continue
            
            try:
                conversation_history.append(HumanMessage(content=user_input))
                response = call_weather_time_agent(model=model, conversation_history= conversation_history)
                ai_response = response["messages"][-1].content
                print(f"Assistant: {ai_response}")
                conversation_history.append(AIMessage(content=ai_response))

            except Exception as e:
                print(f"Error: {e}")
                print("Please try again.")
                continue

    except Exception as e:
        print(f"Error: {e}")
        print("Please try again.")
        

    
                    # Add user message to conversation



if __name__ == "__main__":
    main()
