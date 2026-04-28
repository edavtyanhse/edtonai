from typing import Literal

from backend.core.config import Settings, settings
from backend.integration.ai.base import AIProvider
from backend.integration.ai.deepseek import DeepSeekProvider
from backend.integration.ai.fallback import FallbackProvider
from backend.integration.ai.groq import GroqProvider
from backend.integration.ai.huggingface import HuggingFaceProvider

TaskType = Literal["parsing", "reasoning"]


def get_ai_provider(
    task_type: TaskType = "reasoning",
    app_settings: Settings | None = None,
) -> AIProvider:
    """Factory to get the configured AI provider instance for a specific task.

    Current default: groq (parsing) / deepseek (reasoning).

    To switch to custom edtonai-generator model (GCE VM + Ollama):
      1. Deploy VM: gcloud compute instances create edtonai-inference --zone=us-east1-b
                    --machine-type=e2-medium --provisioning-model=SPOT
      2. Install Ollama, load edtonai-generator-merged GGUF
      3. In Cloud Build trigger set:
             _AI_PROVIDER_PARSING=huggingface
             _AI_PROVIDER_REASONING=huggingface
             _HF_ENDPOINT_URL=http://<VM_INTERNAL_IP>:11434
      4. Re-deploy — done. Groq/DeepSeek remain as automatic fallback.
    """

    config = app_settings or settings

    if task_type == "parsing":
        provider_name = config.ai_provider_parsing.lower()
        groq_model = config.groq_model_parsing
        hf_model = config.hf_model_parsing
    else:
        provider_name = config.ai_provider_reasoning.lower()
        groq_model = config.groq_model_reasoning
        hf_model = config.hf_model_reasoning

    if provider_name == "groq":
        return GroqProvider(
            api_key=config.groq_api_key,
            model=groq_model,
            temperature=config.ai_temperature,
            max_tokens=config.ai_max_tokens,
        )

    elif provider_name == "deepseek":
        return DeepSeekProvider(
            api_key=config.deepseek_api_key,
            base_url=config.deepseek_base_url,
            model=config.ai_model,
            timeout_seconds=config.ai_timeout_seconds,
            max_retries=config.ai_max_retries,
            temperature=config.ai_temperature,
            max_tokens=config.ai_max_tokens,
        )

    elif provider_name == "huggingface":
        hf = HuggingFaceProvider(
            model=hf_model,
            api_key=config.hf_token,
            endpoint_url=config.hf_endpoint_url,
            temperature=config.ai_temperature,
            max_tokens=config.ai_max_tokens,
            max_retries=config.ai_max_retries,
            timeout_seconds=config.ai_timeout_seconds,
        )
        fallback: AIProvider = (
            GroqProvider(
                api_key=config.groq_api_key,
                model=groq_model,
                temperature=config.ai_temperature,
                max_tokens=config.ai_max_tokens,
            )
            if task_type == "parsing"
            else DeepSeekProvider(
                api_key=config.deepseek_api_key,
                base_url=config.deepseek_base_url,
                model=config.ai_model,
                timeout_seconds=config.ai_timeout_seconds,
                max_retries=config.ai_max_retries,
                temperature=config.ai_temperature,
                max_tokens=config.ai_max_tokens,
            )
        )
        return FallbackProvider(primary=hf, fallback=fallback)

    else:
        raise ValueError(f"Unsupported AI provider: {provider_name}")
