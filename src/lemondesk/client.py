"""Lemonade client — talks to Lemonade's OpenAI-compatible API using only stdlib.

Lemonade (https://lemonade-server.ai) default: http://localhost:13305/api/v1
Endpoints used: GET {root}/health (and {base}/health fallback), GET {base}/models,
POST {base}/chat/completions.
"""
from __future__ import annotations
import json, os, time, urllib.request, urllib.error

DEFAULT_BASE = os.environ.get("LEMONADE_BASE_URL", "http://localhost:13305/api/v1")

class LemonadeUnavailable(Exception):
    pass

class LemonadeClient:
    def __init__(self, base_url: str = DEFAULT_BASE, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._models_cache: list | None = None  # populated by list_models()

    def _root(self) -> str:
        return self.base_url[:-len("/api/v1")] if self.base_url.endswith("/api/v1") else self.base_url

    def _get(self, url: str):
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    def _post(self, url: str, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    def health(self) -> bool:
        for url in (f"{self._root()}/health", f"{self.base_url}/health"):
            try:
                self._get(url)
                return True
            except Exception:
                continue
        # Fall back to /models as a liveness probe (some builds expose only /api/v1/*).
        try:
            self.list_models()
            return True
        except Exception:
            return False

    def list_models(self) -> list:
        try:
            data = self._get(f"{self.base_url}/models")
        except Exception as e:
            raise LemonadeUnavailable(f"cannot reach Lemonade at {self.base_url}: {e}") from e
        if isinstance(data, dict) and isinstance(data.get("data"), list):
            models = [m.get("id", str(m)) if isinstance(m, dict) else str(m) for m in data["data"]]
        elif isinstance(data, list):
            models = [m.get("id", str(m)) if isinstance(m, dict) else str(m) for m in data]
        else:
            models = []
        self._models_cache = models
        return models

    def _cached_models(self) -> list:
        """Model list without a network round-trip when already fetched.

        chat() calls this so processing one document (3 chat calls) costs at
        most one /models request instead of one per call (BUG-7 fix). Call
        list_models() directly to force a refresh.
        """
        if self._models_cache is None:
            return self.list_models()
        return self._models_cache

    def chat(self, messages: list, model: str | None = None) -> tuple:
        """Returns (text, model_used). Raises LemonadeUnavailable if unreachable."""
        if model is None:
            models = self._cached_models()
            if not models:
                raise LemonadeUnavailable("Lemonade is running but reports no models")
            model = models[0]
        try:
            data = self._post(f"{self.base_url}/chat/completions",
                              {"model": model, "messages": messages, "temperature": 0.2})
        except Exception as e:
            raise LemonadeUnavailable(f"chat completion failed: {e}") from e
        try:
            return data["choices"][0]["message"]["content"], model
        except Exception as e:
            raise LemonadeUnavailable(f"unexpected Lemonade response shape: {data!r}") from e
