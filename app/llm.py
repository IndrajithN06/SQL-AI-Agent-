import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()


llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    temperature=0,
)
