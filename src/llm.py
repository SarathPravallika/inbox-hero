# cert-aai-2026-06-0061  Sarath Chandra

import json
import time
import urllib.request
import config
from constants import Model

CLIENT = None
LAST = 0.0


def pace() -> None:
    global LAST
    waiting = Model.GAP_SECONDS - (time.monotonic() - LAST)
    if waiting > 0:
        time.sleep(waiting)
    LAST = time.monotonic()


def connect():
    global CLIENT
    if CLIENT is None:
        from google import genai
        if not (config.API_KEY and config.MODEL):
            raise RuntimeError("API_KEY and MODEL have to be set before reaching Gemini")
        CLIENT = genai.Client(api_key=config.API_KEY)
    return CLIENT


def gemini(system: str, text: str, shape: dict) -> list:
    from google.genai import types

    answer = connect().models.generate_content(
        model=config.MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=Model.TEMPERATURE,
            response_mime_type="application/json",
            response_schema=shape,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    return json.loads(answer.text)


def ollama(system: str, text: str, shape: dict) -> list:
    payload = json.dumps({
        "model": config.MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": text}],
        "format": shape,
        "stream": False,
        "options": {"temperature": Model.TEMPERATURE},
    }).encode()
    request = urllib.request.Request(
        config.OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(request, timeout=Model.TIMEOUT_SECONDS) as answer:
        return json.loads(json.loads(answer.read())["message"]["content"])


PROVIDERS = {"gemini": gemini, "ollama": ollama}


def busy(trouble: Exception) -> bool:
    said = str(trouble)
    return any(sign in said for sign in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"))


def ask(system: str, text: str, shape: dict) -> list:
    provider = PROVIDERS.get(config.PROVIDER)
    if provider is None:
        raise RuntimeError(
            f"PROVIDER is {config.PROVIDER!r}, not one of {', '.join(PROVIDERS)}")

    for attempt in range(Model.RETRIES):
        pace()
        try:
            return provider(system, text, shape)
        except Exception as trouble:
            if attempt == Model.RETRIES - 1 or not busy(trouble):
                raise
            time.sleep(Model.BACKOFF_SECONDS * (attempt + 1))
