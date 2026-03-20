from __future__ import annotations

from agents.guardrail import GuardrailFunctionOutput, input_guardrail

from app.services.security import SENSITIVE_REFUSAL_MESSAGE, user_requests_sensitive_disclosure


@input_guardrail(name="no_credential_disclosure", run_in_parallel=False)
def no_credential_disclosure_guardrail(context, agent, input):
    """
    OpenAI Agents SDK-style input guardrail.
    If the user requests password/secret/credential disclosure, halt the run.
    """
    text = input if isinstance(input, str) else ""

    if user_requests_sensitive_disclosure(text):
        return GuardrailFunctionOutput(
            output_info={"error": SENSITIVE_REFUSAL_MESSAGE},
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(
        output_info={"ok": True},
        tripwire_triggered=False,
    )

