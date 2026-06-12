"""
Service pour la gestion du modèle de langage (LLM)
"""

import asyncio
import logging

import requests
from requests import RequestException

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service pour gérer l'interaction avec Ollama en local."""

    _instance = None
    _initialized = False

    def __new__(cls):
        """Pattern Singleton pour partager une seule instance de service."""
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        """Prépare la configuration Ollama une seule fois au démarrage."""
        if LLMService._initialized:
            return

        ollama_model = getattr(settings, "OLLAMA_MODEL", "phi3:mini")
        ollama_url = getattr(settings, "OLLAMA_URL", "http://localhost:11434")
        logger.info(
            "Utilisation d'Ollama local: modele=%s url=%s",
            ollama_model,
            ollama_url,
        )
        LLMService._initialized = True

    def _generate_sync(self, prompt: str) -> str:
        """Appelle l'API Ollama locale de manière synchrone."""
        ollama_url = getattr(settings, "OLLAMA_URL", "http://localhost:11434")
        ollama_model = getattr(settings, "OLLAMA_MODEL", "phi3:mini")
        ollama_timeout = getattr(settings, "OLLAMA_TIMEOUT", 120)
        max_new_tokens = getattr(settings, "MAX_NEW_TOKENS", 50)
        temperature = getattr(settings, "TEMPERATURE", 0.7)
        top_p = getattr(settings, "TOP_P", 0.9)
        response = requests.post(
            f"{ollama_url.rstrip('/')}/api/generate",
            json={
                "model": ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_new_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                },
            },
            timeout=ollama_timeout,
        )
        response.raise_for_status()

        data = response.json()
        generated_text = data.get("response", "").strip()
        if not generated_text:
            raise RuntimeError("Réponse Ollama vide")

        return generated_text

    async def generate_response(self, prompt: str) -> str:
        """
        Génère une réponse basée sur le prompt fourni via Ollama local.

        Args:
            prompt: Le texte d'entrée pour la génération

        Returns:
            str: Le texte généré

        Raises:
            Exception: Si une erreur survient lors de la génération
        """
        try:
            if not LLMService._initialized:
                self.initialize()

            return await asyncio.to_thread(self._generate_sync, prompt)
        except RequestException as e:
            logger.error("Erreur de connexion à Ollama: %s", e)
            raise RuntimeError("Impossible de joindre Ollama local") from e
        except Exception as e:
            logger.error("Erreur lors de la génération de réponse: %s", e)
            raise


# Instance unique du service
llm_service = LLMService()
