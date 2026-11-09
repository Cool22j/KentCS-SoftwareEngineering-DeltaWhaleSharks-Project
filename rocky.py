"""Rocky client using LangChain ChatPromptTemplate, RunnableLambda, and JsonOutputParser."""

import json
import os
import time
import requests
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import RunnableLambda

load_dotenv()

ROCKY_MODELS_URL = "https://rocky.cs.kent.edu/v1/models"
ROCKY_RESPONSES_URL = "https://rocky.cs.kent.edu/v1/responses"
TRANSIENT_STATUS_CODES = {502, 503, 504}
_CACHED_ROCKY_MODEL = None

# 1. Initialize LangChain output parser
_json_parser = JsonOutputParser()

# 2. Concise template separating system role from user prompt
_json_prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        "Respond immediately with ONLY a valid JSON object formatted as: "
        '{{"query": "short summary", "output": ...}}. '
        "Do not wrap in markdown code fences."
    ),
    ("user", "{prompt}"),
])


def _get_rocky_headers(headers=None):
    """Build Authorization headers for Rocky using ROCKY_API_KEY."""
    api_key = os.getenv("ROCKY_API_KEY", "").strip()
    if api_key:
        return {"Authorization": f"Bearer {api_key}"}
    if isinstance(headers, dict) and headers.get("Authorization"):
        return headers
    raise RuntimeError("ROCKY_API_KEY is not set in your .env file.")


def get_model(headers=None):
    """Fetch and cache the active model ID from Rocky."""
    global _CACHED_ROCKY_MODEL
    if _CACHED_ROCKY_MODEL:
        return _CACHED_ROCKY_MODEL

    req_headers = _get_rocky_headers(headers)
    response = requests.get(ROCKY_MODELS_URL, headers=req_headers, timeout=30)
    response.raise_for_status()

    models = response.json().get("data", [])
    if not models:
        raise RuntimeError("Rocky returned no available models.")

    _CACHED_ROCKY_MODEL = models[0]["id"]
    return _CACHED_ROCKY_MODEL


def _extract_response_text(data):
    """Extract the assistant text from Rocky's /v1/responses payload."""
    if not isinstance(data, dict):
        return ""
    text = data.get("output_text")
    if not text:
        parts = []
        for item in data.get("output", []):
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("text"), str) and item.get("type") == "output_text":
                parts.append(item["text"])
            for part in item.get("content", []):
                if isinstance(part, dict) and part.get("text") and part.get("type") in ("output_text", "text", None):
                    parts.append(part["text"])
        text = "\n".join(parts)
    return (text or "").strip()


def _read_stream_or_json(response):
    """Read SSE stream (or plain JSON) from Rocky so the reverse proxy never 504s."""
    content_type = response.headers.get("Content-Type", "")
    if "text/event-stream" not in content_type:
        text = _extract_response_text(response.json())
        if not text:
            raise ValueError("Rocky returned a response with no output text.")
        return text

    deltas = []
    done_texts = []
    completed_payload = None

    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        line = raw_line.strip()
        if not line.startswith("data:"):
            continue
        data_str = line[5:].strip()
        if not data_str or data_str == "[DONE]":
            continue
        try:
            evt = json.loads(data_str)
        except ValueError:
            continue
        if not isinstance(evt, dict):
            continue

        evt_type = evt.get("type", "")
        if evt_type == "response.output_text.delta" and isinstance(evt.get("delta"), str):
            deltas.append(evt["delta"])
        elif evt_type == "response.output_text.done" and isinstance(evt.get("text"), str):
            done_texts.append(evt["text"])
        elif evt_type == "response.content_part.done" and isinstance(evt.get("part"), dict):
            part_text = evt["part"].get("text")
            if isinstance(part_text, str) and part_text:
                done_texts.append(part_text)
        elif evt_type == "response.output_item.done" and isinstance(evt.get("item"), dict):
            extracted = _extract_response_text({"output": [evt["item"]]})
            if extracted:
                done_texts.append(extracted)
        elif evt_type in ("response.completed", "response.done", "response.incomplete") and isinstance(evt.get("response"), dict):
            completed_payload = evt["response"]
        elif "output" in evt or "output_text" in evt:
            completed_payload = evt

    if deltas:
        return "".join(deltas).strip()
    if done_texts:
        return "\n".join(done_texts).strip()
    if completed_payload:
        extracted = _extract_response_text(completed_payload)
        if extracted:
            return extracted
    raise ValueError("Rocky stream ended without output text.")


def parse_json_response(text):
    """Parse the LLM's JSON string using LangChain's JsonOutputParser."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("LLM returned an empty response.")

    try:
        data = _json_parser.parse(text)
    except OutputParserException as exc:
        raise ValueError(f"Failed to parse model output as JSON: {exc}") from exc

    if not isinstance(data, dict) or "query" not in data or "output" not in data:
        raise ValueError("Response JSON must contain 'query' and 'output' keys.")
    return data


def ask_rocky_json(prompt, model=None, headers=None, max_completion_tokens=6144):
    """Run an LCEL chain (ChatPromptTemplate | Rocky RunnableLambda | JsonOutputParser)."""
    req_headers = _get_rocky_headers(headers)
    target_model = model or get_model(req_headers)

    # Allocate at least 6144 tokens (up to Rocky's 8192 limit) because qwen3.8-27b
    # counts internal reasoning_tokens toward max_output_tokens.
    token_budget = max(6144, min(max_completion_tokens, 8192))

    def _call_rocky(prompt_value):
        messages = prompt_value.to_messages()
        instructions = messages[0].content if len(messages) > 1 else ""
        user_input = messages[-1].content if messages else str(prompt)

        payload = {
            "model": target_model,
            "instructions": instructions,
            "input": user_input,
            "max_output_tokens": token_budget,
            "stream": True,
            "store": False,
        }
        last_err = None
        for attempt in range(2):
            try:
                with requests.post(
                    ROCKY_RESPONSES_URL,
                    headers=req_headers,
                    json=payload,
                    stream=True,
                    timeout=(15, 240),
                ) as response:
                    if response.status_code in TRANSIENT_STATUS_CODES and attempt < 1:
                        time.sleep(3)
                        continue
                    response.raise_for_status()
                    return _read_stream_or_json(response)
            except (requests.RequestException, ValueError) as exc:
                last_err = exc
                if attempt < 1:
                    time.sleep(2)
                    continue
                raise
        raise RuntimeError(f"Rocky failed: {last_err}")

    chain = _json_prompt_template | RunnableLambda(_call_rocky) | _json_parser

    try:
        data = chain.invoke({"prompt": prompt})
    except OutputParserException as exc:
        raise ValueError(f"Failed to parse structured JSON from Rocky: {exc}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Error communicating with Rocky: {exc}") from exc

    if not isinstance(data, dict) or "query" not in data or "output" not in data:
        raise ValueError("Response JSON must contain 'query' and 'output' keys.")

    return data
