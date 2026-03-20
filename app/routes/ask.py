import uuid
import time
import logging

from fastapi import APIRouter
from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered

from app.models.schemas import AskRequest
from app.services.agent_builder import build_agent
from app.services.security import (
    redact_secrets,
)
from app.core.config import run_config

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ask/{agent_id}")
async def ask_agent(agent_id: int, data: AskRequest):

    request_id = str(uuid.uuid4())
    start_time = time.time()

    logger.info(f"[{request_id}] Incoming query for agent_id={agent_id}")
    redacted_question = redact_secrets(data.question)
    logger.info(f"[{request_id}] Question: {redacted_question}")

    # -----------------------------
    # Build Agent
    # -----------------------------
    agent = build_agent(agent_id, request_id=request_id)

    if not agent:
        logger.warning(f"[{request_id}] Agent not found: {agent_id}")
        return {"error": "Agent not found"}

    try:
        # -----------------------------
        # Run Agent
        # -----------------------------
        try:
            result = await Runner.run(
                starting_agent=agent,
                input=redacted_question,
                run_config=run_config
            )
        except InputGuardrailTripwireTriggered as e:
            guardrail_info = (
                e.guardrail_result.output.output_info
                if getattr(e, "guardrail_result", None) is not None
                else None
            )
            message = (
                guardrail_info.get("error")
                if isinstance(guardrail_info, dict) and guardrail_info.get("error")
                else "Request blocked by input guardrail"
            )
            return {
                "request_id": request_id,
                "agent_id": None,
                "agent_name": "Guardrail",
                "response": message,
                "error": message,
            }

        final_agent = result.last_agent

        agent_name = final_agent.name if final_agent else "Unknown"

        #  Extract agent_id from metadata
        agent_id_response = (
        getattr(final_agent, "agent_id", None)
        if final_agent else None
    )

        output = result.final_output

        duration = round(time.time() - start_time, 3)

        logger.info(f"[{request_id}] Completed in {duration}s")
        logger.info(f"[{request_id}] Responded by: {agent_name} (ID: {agent_id_response})")

        output = redact_secrets(output)

        return {
            "request_id": request_id,
            "agent_id": agent_id_response,
            "agent_name": agent_name,
            "response": output
        }

    except Exception as e:
        duration = round(time.time() - start_time, 3)

        logger.error(
            f"[{request_id}] ERROR after {duration}s: {str(e)}",
            exc_info=True
        )

        return {
            "request_id": request_id,
            "error": "Internal server error"
        }