import os
import time
import requests
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


from tools import get_weather

#Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_MODEL"] = os.getenv("OPENAI_MODEL")

# Initialize the model
model = ChatOpenAI(model=os.environ["OPENAI_MODEL"], temperature=0)

def main():
    print("Hello from agents-observation!")
    print(get_weather.invoke("Isfahan"))


if __name__ == "__main__":
    main()
