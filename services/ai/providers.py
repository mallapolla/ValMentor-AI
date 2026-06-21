import logging
from django.conf import settings
from strands.models.anthropic import AnthropicModel
# Litellm / Gemini fallback client or custom LLM bindings
from litellm import completion

logger = logging.getLogger(__name__)

class LitellmModelWrapper:
    """
    Fallback Model Wrapper that acts similarly to Strands Agent models.
    Invokes LiteLLM to support Google Gemini and other models transparently.
    """
    def __init__(self, model_id: str, api_key: str, max_tokens: int, temperature: float):
        self.model_id = model_id
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature

    def __call__(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = completion(
                model=self.model_id,
                messages=messages,
                api_key=self.api_key,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LiteLLM invocation failed: {e}")
            raise e

class AIProviderFactory:
    """
    Factory to retrieve configured Strands model provider or fallback client.
    Supports Anthropic Claude and Google Gemini configuration.
    """
    @staticmethod
    def get_model():
        provider = settings.AI_PROVIDER.lower()
        
        if provider == 'anthropic':
            if not settings.ANTHROPIC_API_KEY:
                logger.warning("ANTHROPIC_API_KEY not configured. Falling back to Gemini/LiteLLM.")
                return AIProviderFactory._get_gemini_model()
            try:
                # Initialize AnthropicModel provider from Strands Agents SDK
                return AnthropicModel(
                    client_args={
                        "api_key": settings.ANTHROPIC_API_KEY,
                    },
                    model_id=settings.AI_MODEL_ID or "claude-3-5-sonnet-20241022",
                    max_tokens=settings.AI_MAX_TOKENS,
                    params={
                        "temperature": settings.AI_TEMPERATURE,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to load Anthropic model: {e}. Falling back to Gemini.")
                return AIProviderFactory._get_gemini_model()
        else:
            return AIProviderFactory._get_gemini_model()

    @staticmethod
    def _get_gemini_model():
        """Returns native Strands Gemini model with fallback to LiteLLM wrapper."""
        from strands.models.gemini import GeminiModel
        model_id = settings.AI_MODEL_ID
        if not model_id or "claude" in model_id:
            model_id = "gemini-1.5-flash"
        
        api_key = settings.GOOGLE_API_KEY
        try:
            return GeminiModel(
                client_args={
                    "api_key": api_key,
                },
                model_id=model_id,
                params={
                    "temperature": settings.AI_TEMPERATURE,
                    "max_output_tokens": settings.AI_MAX_TOKENS,
                }
            )
        except Exception as e:
            logger.error(f"Failed to initialize native Gemini model: {e}. Falling back to LiteLLM wrapper.")
            # Fallback to LitellmModelWrapper (using prefix 'gemini/' for litellm)
            litellm_model_id = f"gemini/{model_id}" if not model_id.startswith("gemini/") else model_id
            return LitellmModelWrapper(
                model_id=litellm_model_id,
                api_key=api_key,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )

