from __future__ import annotations

import os
from typing import Any, Optional

from flask import current_app

try:
	from openai import OpenAI
except Exception:  # pragma: no cover
	OpenAI = None  # type: ignore

try:
	import anthropic
except Exception:  # pragma: no cover
	anthropic = None  # type: ignore

try:
	from langchain_groq import ChatGroq
	from langchain.prompts import PromptTemplate

except Exception: # pragma: no cover
	ChatGroq = None


def get_openai_client() -> Any:
	api_key = current_app.config.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
	if not api_key or OpenAI is None:
		raise RuntimeError("OpenAI client not configured or library missing")
	return OpenAI(api_key=api_key)


def get_anthropic_client() -> Any:
	api_key = current_app.config.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
	if not api_key or anthropic is None:
		raise RuntimeError("Anthropic client not configured or library missing")
	return anthropic.Anthropic(api_key=api_key)

def get_groq_llm() -> Any:
	api_key = current_app.config.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
	api_model = current_app.config.get("GROQ_MODEL_NAME") or os.getenv("GROQ_MODEL_NAME")
	llm = ChatGroq(model_name=api_model,
					groq_api_key=api_key,
					temperature=0.3)
	return llm


def safe_openai_complete(prompt: str, model: str = "gpt-4o-mini") -> str:
	"""Minimal safe wrapper for OpenAI text completion/chat."""
	client = get_openai_client()
	try:
		resp = client.chat.completions.create(
			model=model,
			messages=[{"role": "user", "content": prompt}],
			temperature=0.2,
		)
		return resp.choices[0].message.content or ""
	except Exception as exc:  # noqa: BLE001
		current_app.logger.error("OpenAI error: %s", exc)
		return ""


def safe_anthropic_complete(prompt: str, model: str = "claude-3-5-sonnet-20240620") -> str:
	"""Minimal safe wrapper for Anthropic messages API."""
	client = get_anthropic_client()
	try:
		resp = client.messages.create(
			model=model,
			max_tokens=512,
			messages=[{"role": "user", "content": prompt}],
		)
		# Anthropic returns a list of content blocks
		parts = resp.content or []
		text = "".join(
			p.text for p in parts if getattr(p, "type", None) == "text" and getattr(p, "text", None)
		)
		return text
	except Exception as exc:  # noqa: BLE001
		current_app.logger.error("Anthropic error: %s", exc)
		return ""

GROQ_TEMPLATE = "\n".join([
    "Please politely reply to the client"
    "{message}",
])
def safe_groq_complete(prompt: str) -> str:
	"""Minimal safe wrapper for Groq messages API."""
	llm = get_groq_llm()
	try:
		groq_template = PromptTemplate(
			input_variables = ["message"],
			template = GROQ_TEMPLATE
		)
		client = groq_template | llm
		result_string = client.invoke({"message": prompt}).content
		return result_string
		pass
	except Exception as exc:  # noqa: BLE001
		current_app.logger.error("Groq error: %s", exc)
		return ""

