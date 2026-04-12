from typing import Literal

from backend.core.config import settings
from backend.integration.ai.base import AIProvider
from backend.integration.ai.deepseek import DeepSeekProvider
from backend.integration.ai.fallback import FallbackProvider
from backend.integration.ai.groq import GroqProvider
from backend.integration.ai.huggingface import HuggingFaceProvider

TaskType = Literal["parsing", "reasoning"]


def get_ai_provider(task_type: TaskType = "reasoning") -> AIProvider:
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

    if task_type == "parsing":
        provider_name = settings.ai_provider_parsing.lower()
        groq_model = settings.groq_model_parsing
        hf_model = settings.hf_model_parsing
    else:
        provider_name = settings.ai_provider_reasoning.lower()
        groq_model = settings.groq_model_reasoning
        hf_model = settings.hf_model_reasoning

    if provider_name == "groq":
        return GroqProvider(model=groq_model)

    elif provider_name == "deepseek":
        return DeepSeekProvider()

    elif provider_name == "huggingface":
        hf = HuggingFaceProvider(
            model=hf_model,
            api_key=settings.hf_token,
            endpoint_url=settings.hf_endpoint_url,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            max_retries=settings.ai_max_retries,
            timeout_seconds=settings.ai_timeout_seconds,
        )
        fallback: AIProvider = (
            GroqProvider(model=groq_model)
            if task_type == "parsing"
            else DeepSeekProvider()
        )
        return FallbackProvider(primary=hf, fallback=fallback)

    else:
        raise ValueError(f"Unsupported AI provider: {provider_name}")
