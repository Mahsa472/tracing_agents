from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from tools import get_weather, get_current_time
from pathlib import Path



def load_prompt(prompt_file: str) -> str:
    """Load a prompt from a file."""
    root = Path(__file__).resolve().parent.parent
    path = root / "prompts" / "system" / f"{prompt_file}.md"
    return path.read_text(encoding="utf-8").strip()

def call_weather_time_agent(model, conversation_history):
    weather_time_agent = create_agent(
        model=model,
        tools=[get_weather, get_current_time],
        system_prompt=load_prompt("base"),
        )

    return weather_time_agent.invoke({
        "messages": conversation_history
        })