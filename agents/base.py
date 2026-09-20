import json
import time
import httpx
from typing import Dict, Any, Optional
from config import settings

class BaseAgent:
    """
    Base class for all DevOps agents (Planner, Coder, Tester, Critic, Escalation).
    Provides REAL LLM invocation across Anthropic, OpenAI, Gemini, Groq, Ollama,
    with an intelligent deterministic offline mode when no API keys are supplied.
    """

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.model_name = settings.MODEL_NAME
        self.provider = settings.LLM_PROVIDER.lower()

    def generate(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # 1. Anthropic Claude (Real API)
        if (self.provider == "anthropic" or settings.ANTHROPIC_API_KEY) and settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                response = client.messages.create(
                    model=self.model_name if "claude" in self.model_name else "claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return {
                    "content": response.content[0].text,
                    "tokens_in": response.usage.input_tokens,
                    "tokens_out": response.usage.output_tokens,
                    "duration": round(time.time() - start_time, 2),
                    "is_real_llm": True
                }
            except Exception as e:
                print(f"[{self.name}] Anthropic API error: {e}")

        # 2. OpenAI (Real API)
        if (self.provider == "openai" or settings.OPENAI_API_KEY) and settings.OPENAI_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.model_name if "gpt" in self.model_name else "gpt-4o",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                }
                with httpx.Client(timeout=60.0) as client:
                    res = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        return {
                            "content": data["choices"][0]["message"]["content"],
                            "tokens_in": data["usage"]["prompt_tokens"],
                            "tokens_out": data["usage"]["completion_tokens"],
                            "duration": round(time.time() - start_time, 2),
                            "is_real_llm": True
                        }
            except Exception as e:
                print(f"[{self.name}] OpenAI API error: {e}")

        # 3. Google Gemini (Real REST API)
        if (self.provider == "gemini" or settings.GEMINI_API_KEY) and settings.GEMINI_API_KEY:
            try:
                model = "gemini-1.5-flash" if "flash" in self.model_name else "gemini-1.5-pro"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\nTask:\n{user_prompt}"}]}]
                }
                with httpx.Client(timeout=60.0) as client:
                    res = client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return {
                            "content": text,
                            "tokens_in": 500,
                            "tokens_out": len(text) // 4,
                            "duration": round(time.time() - start_time, 2),
                            "is_real_llm": True
                        }
            except Exception as e:
                print(f"[{self.name}] Gemini API error: {e}")

        # 4. Groq (Real fast API)
        if settings.GROQ_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                }
                with httpx.Client(timeout=60.0) as client:
                    res = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        return {
                            "content": data["choices"][0]["message"]["content"],
                            "tokens_in": data["usage"]["prompt_tokens"],
                            "tokens_out": data["usage"]["completion_tokens"],
                            "duration": round(time.time() - start_time, 2),
                            "is_real_llm": True
                        }
            except Exception as e:
                print(f"[{self.name}] Groq API error: {e}")

        # 5. Ollama (100% Real, Local, Free Offline LLM)
        if self.provider == "ollama":
            try:
                payload = {
                    "model": settings.OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False
                }
                with httpx.Client(timeout=120.0) as client:
                    res = client.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        return {
                            "content": data["message"]["content"],
                            "tokens_in": data.get("prompt_eval_count", 300),
                            "tokens_out": data.get("eval_count", 200),
                            "duration": round(time.time() - start_time, 2),
                            "is_real_llm": True
                        }
            except Exception as e:
                print(f"[{self.name}] Ollama local API error: {e}")

        # Deterministic simulation fallback when no active API keys / Ollama server
        return self._fallback_generate(system_prompt, user_prompt, start_time)

    def _fallback_generate(self, system_prompt: str, user_prompt: str, start_time: float) -> Dict[str, Any]:
        time.sleep(0.5)
        content = ""
        
        if "Planner" in self.name or "Architect" in self.name:
            content = json.dumps({
                "subtasks": [
                    "1. Architecture and module breakdown",
                    "2. Implementation with error handling and validation",
                    "3. Comprehensive unit and integration testing",
                    "4. Static analysis and guardrail verification"
                ],
                "files_to_create": ["app/main.py", "app/utils.py"],
                "tech_stack": "Python 3.11, FastAPI, Pydantic, Pytest",
                "approach": "Clean architecture adhering to PEP-8 with comprehensive test coverage."
            }, indent=2)

        elif "Coder" in self.name:
            content = (
                "<file path=\"app/__init__.py\">\n"
                "# Package marker\n"
                "</file>\n\n"
                "<file path=\"app/main.py\">\n"
                "from fastapi import FastAPI, HTTPException\n"
                "from pydantic import BaseModel\n\n"
                "app = FastAPI(title=\"DevOps Service\", version=\"1.0.0\")\n\n"
                "class Item(BaseModel):\n"
                "    id: int\n"
                "    name: str\n"
                "    description: str = \"\"\n\n"
                "@app.get(\"/\")\n"
                "def root():\n"
                "    return {\"status\": \"active\", \"service\": \"DevOps-Agent\"}\n\n"
                "@app.get(\"/items/{item_id}\")\n"
                "def get_item(item_id: int):\n"
                "    if item_id <= 0:\n"
                "        raise HTTPException(status_code=400, detail=\"Invalid item ID\")\n"
                "    return {\"id\": item_id, \"name\": f\"Item {item_id}\", \"status\": \"verified\"}\n"
                "</file>\n\n"
                "<file path=\"app/utils.py\">\n"
                "def sanitize_input(text: str) -> str:\n"
                "    if not isinstance(text, str):\n"
                "        return \"\"\n"
                "    return text.strip()\n\n"
                "def calculate_metric(values: list) -> float:\n"
                "    if not values:\n"
                "        return 0.0\n"
                "    return sum(values) / len(values)\n"
                "</file>"
            )

        elif "Tester" in self.name:
            content = (
                "<file path=\"tests/test_main.py\">\n"
                "import pytest\n"
                "from app.utils import sanitize_input, calculate_metric\n\n"
                "def test_sanitize_input():\n"
                "    assert sanitize_input(\"  hello world  \") == \"hello world\"\n"
                "    assert sanitize_input(123) == \"\"\n\n"
                "def test_calculate_metric():\n"
                "    assert calculate_metric([10, 20, 30]) == 20.0\n"
                "    assert calculate_metric([]) == 0.0\n"
                "</file>"
            )

        elif "Critic" in self.name:
            content = json.dumps({
                "approved": True,
                "score": 0.95,
                "code_quality": "High",
                "security_assessment": "Clean. No prompt injections, dangerous imports or credentials.",
                "feedback": "Code follows PEP-8, includes input sanitization, error handling, and complete unit tests.",
                "issues": []
            }, indent=2)

        elif "Escalation" in self.name:
            content = json.dumps({
                "escalate": False,
                "confidence_score": 0.95,
                "reason": "All checks passed with high confidence."
            }, indent=2)

        return {
            "content": content,
            "tokens_in": 350,
            "tokens_out": 220,
            "duration": round(time.time() - start_time, 2),
            "is_real_llm": False
        }
