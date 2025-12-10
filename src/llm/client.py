"""LLM-klient för OpenRouter API.

Hanterar kommunikation med LLM för känslighetsbedömning och rollidentifiering.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Konfiguration för LLM-klient."""

    api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    model: str = "openai/gpt-4o-mini"  # Snabb och kostnadseffektiv
    temperature: float = 0.1  # Låg för konsistenta svar
    max_tokens: int = 2000
    timeout: int = 60
    site_url: str = "https://menprovning.se"
    site_name: str = "Menprovningsverktyg"


@dataclass
class LLMResponse:
    """Svar från LLM."""

    content: str
    model: str
    usage: dict = field(default_factory=dict)
    raw_response: dict = field(default_factory=dict)


class LLMClient:
    """
    Klient för OpenRouter LLM API.

    Hanterar:
    - API-anrop med autentisering
    - Felhantering och retries
    - Strukturerade svar
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initiera LLM-klient.

        Args:
            config: Konfiguration för klienten
        """
        self.config = config or LLMConfig()

        if not self.config.api_key:
            logger.warning(
                "Ingen API-nyckel konfigurerad. "
                "Sätt OPENROUTER_API_KEY miljövariabel."
            )

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        """
        Skicka chattmeddelande till LLM.

        Args:
            messages: Lista med meddelanden [{"role": "user", "content": "..."}]
            system_prompt: Systemmeddelande (läggs till först)
            temperature: Temperatur för sampling
            max_tokens: Max antal tokens i svaret
            response_format: Format för svaret (t.ex. {"type": "json_object"})

        Returns:
            LLMResponse med svaret

        Raises:
            LLMError: Vid fel i API-anrop
        """
        from src.core.exceptions import LLMError

        if not self.config.api_key:
            raise LLMError("Ingen API-nyckel konfigurerad")

        # Bygg meddelandelista
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        # Bygg request
        payload = {
            "model": self.config.model,
            "messages": all_messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.config.site_url,
            "X-Title": self.config.site_name,
        }

        try:
            response = requests.post(
                self.config.base_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=self.config.timeout,
            )

            response.raise_for_status()
            data = response.json()

            # Extrahera svar
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=data.get("model", self.config.model),
                usage=usage,
                raw_response=data,
            )

        except requests.exceptions.Timeout:
            raise LLMError(f"Timeout efter {self.config.timeout} sekunder")
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", str(e))
            except Exception:
                pass
            raise LLMError(f"HTTP-fel: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise LLMError(f"Nätverksfel: {e}")
        except (KeyError, IndexError) as e:
            raise LLMError(f"Oväntat svarsformat: {e}")

    def chat_json(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Skicka chattmeddelande och få JSON-svar.

        Args:
            messages: Lista med meddelanden
            system_prompt: Systemmeddelande
            temperature: Temperatur för sampling

        Returns:
            Parsad JSON som dict

        Raises:
            LLMError: Vid fel i API-anrop eller JSON-parsning
        """
        from src.core.exceptions import LLMError
        import re

        # Vissa modeller stöder inte response_format, prova utan om det misslyckas
        response = self.chat(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=3000,  # Öka för att undvika avklippta svar
        )

        content = response.content.strip()

        # Försök parsa direkt
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Försök extrahera JSON från markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Försök hitta JSON-objekt i texten
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Sista utväg: returnera ett standardsvar
        logger.warning(f"Kunde inte parsa LLM-svar som JSON, returnerar standardvärden. Svar: {content[:200]}...")
        return {
            "primary_category": "NEUTRAL",
            "sensitivity_level": "MEDIUM",
            "recommended_action": "ASSESS",
            "confidence": 0.5,
            "reasons": ["LLM-svar kunde inte parsas"],
        }

    def analyze_text(
        self,
        text: str,
        prompt_template: str,
        **kwargs: Any,
    ) -> str:
        """
        Analysera text med given prompt-mall.

        Args:
            text: Texten att analysera
            prompt_template: Prompt-mall med {text} placeholder
            **kwargs: Extra variabler för prompt-mallen

        Returns:
            LLM:s analys som sträng
        """
        prompt = prompt_template.format(text=text, **kwargs)

        response = self.chat(
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content

    def is_configured(self) -> bool:
        """Kontrollera om klienten är korrekt konfigurerad."""
        return bool(self.config.api_key)

    def test_connection(self) -> bool:
        """
        Testa anslutningen till API:et.

        Returns:
            True om anslutningen fungerar
        """
        try:
            response = self.chat(
                messages=[{"role": "user", "content": "Svara endast med 'OK'."}],
                max_tokens=10,
            )
            return "OK" in response.content.upper()
        except Exception as e:
            logger.error(f"Anslutningstest misslyckades: {e}")
            return False

    def get_model_info(self) -> dict:
        """Hämta information om konfigurerad modell."""
        return {
            "model": self.config.model,
            "configured": self.is_configured(),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
