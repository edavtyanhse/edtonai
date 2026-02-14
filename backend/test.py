import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ai import DeepSeekProvider
from backend.core.logging import setup_logging

setup_logging()

async def test():
    provider = DeepSeekProvider()
    result = await provider.generate_json(
        prompt='Верни JSON: {"test": true}',
        prompt_name="test_prompt"
    )
    print(result)

asyncio.run(test())
