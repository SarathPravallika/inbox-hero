# cert-aai-2026-06-0061  Sarath Chandra

import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")
PROVIDER = os.getenv("PROVIDER", "gemini")
