# cert-aai-2026-06-0061  Sarath Chandra
#
# - Reads the model provider settings from the environment
# - Keeps the API key out of the code and out of the repository

import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")
PROVIDER = os.getenv("PROVIDER", "gemini")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
