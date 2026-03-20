import os
import logging
from dotenv import load_dotenv

from agents import AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig

load_dotenv()
logger = logging.getLogger(__name__)

from app.services.input_guardrails import no_credential_disclosure_guardrail

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found")

# OpenRouter client
client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

# Model
model = OpenAIChatCompletionsModel(
    model="meta-llama/llama-3-8b-instruct",
    openai_client=client
)

# Run config
run_config = RunConfig(
    model=model,
    model_provider=client,
    input_guardrails=[no_credential_disclosure_guardrail],
    tracing_disabled=False
)