#!/usr/bin/env python3

import json
import urllib.error
import urllib.request


DEFAULT_MODEL = "qwen3:1.7b"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"


SYSTEM_PROMPT = """
You are Webbie, the resident AI built into Spider OS.

You are part of the operating system, not a website.

Your primary user is Cory.

Use the name:
- Cory normally.
- Justin inside Studio.
- Spider inside Kali Bay.

Be concise when responding by voice.
Be more detailed when responding in the graphical interface.

You help operate Spider OS, organize information, work with Forage and
Deep Forage, launch workspaces, support study and creative work, and
assist with normal computer tasks.

Never claim an action succeeded unless Spider OS actually performed it.
""".strip()


def ask_ollama(message, context_name="Cory", model=DEFAULT_MODEL):
    prompt = (
        SYSTEM_PROMPT
        + "\n\nCurrent user name: "
        + context_name
    )

    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": message,
            },
        ],
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=120,
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        return (
            data.get("message", {})
            .get("content", "")
            .strip()
        )

    except (
        urllib.error.URLError,
        TimeoutError,
        ValueError,
        KeyError,
    ):
        return None


def built_in_response(message, context_name="Cory"):
    lower = message.lower().strip()

    if lower in {
        "hello",
        "hi",
        "hey",
    }:
        return f"Hey {context_name}. I'm here."

    if "who are you" in lower:
        return (
            "I'm Webbie, the resident AI inside Spider OS."
        )

    if "what are you" in lower:
        return (
            "I'm Webbie, the resident AI layer of Spider OS."
        )

    return (
        f"I heard you, {context_name}. "
        "My local language model is not online yet, "
        "but my Spider OS controls are available."
    )


def respond(message, context_name="Cory"):
    answer = ask_ollama(
        message,
        context_name=context_name,
    )

    if answer:
        return answer

    return built_in_response(
        message,
        context_name=context_name,
    )
