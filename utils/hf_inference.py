#!/usr/bin/env python3
"""Lightweight Hugging Face Inference client (serverless)."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class HFResponse:
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    model: Optional[str] = None


def _get_hf_token() -> Optional[str]:
    token = os.getenv("HF_API_TOKEN")
    if token:
        return token
    try:
        import streamlit as st  # type: ignore
        return st.secrets.get("HF_API_TOKEN")
    except Exception:
        return None


class HFInferenceClient:
    def __init__(self, token: Optional[str] = None, timeout_s: int = 30):
        self.token = token or _get_hf_token()
        self.timeout_s = timeout_s

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def infer(self, model: str, payload: Dict[str, Any]) -> HFResponse:
        if not self.token:
            return HFResponse(ok=False, error="HF_API_TOKEN not set", model=model)

        url = f"https://api-inference.huggingface.co/models/{model}"
        try:
            resp = requests.post(url, headers=self._headers(), json=payload, timeout=self.timeout_s)
            if resp.status_code == 503:
                # Model loading on first request
                try:
                    wait_s = resp.json().get("estimated_time", 10)
                except Exception:
                    wait_s = 10
                time.sleep(min(wait_s, 20))
                resp = requests.post(url, headers=self._headers(), json=payload, timeout=self.timeout_s)

            if resp.status_code >= 400:
                return HFResponse(ok=False, error=f"{resp.status_code}: {resp.text[:200]}", model=model)

            return HFResponse(ok=True, data=resp.json(), model=model)
        except Exception as e:
            return HFResponse(ok=False, error=str(e), model=model)

    def summarize(self, text: str, model: str, max_length: int = 180, min_length: int = 40) -> HFResponse:
        payload = {
            "inputs": text,
            "parameters": {
                "max_length": max_length,
                "min_length": min_length,
                "do_sample": False,
            },
        }
        return self.infer(model, payload)

    def sentiment(self, text: str, model: str) -> HFResponse:
        payload = {"inputs": text}
        return self.infer(model, payload)

    def extract_risks(self, text: str, model: str) -> HFResponse:
        prompt = (
            "Extract key risks and red flags from the following text. "
            "Return a short bullet list in Turkish:\n\n" + text
        )
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.2,
                "do_sample": False,
            },
        }
        return self.infer(model, payload)
