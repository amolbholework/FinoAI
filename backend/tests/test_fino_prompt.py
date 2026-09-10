"""Guardrails are enforced by the model via the system prompt, not by code —
so the testable contract here is that the required guardrail language is
actually present in the composed prompt, and that it's identical to what
the advice panel uses (shared_prompt.py), which is the whole point of
having one shared builder."""
from app.ai.fino_prompt import build_fino_system_prompt
from app.ai.prompt import SYSTEM_PROMPT as ADVICE_PANEL_PROMPT
from app.ai.shared_prompt import GUARDRAILS_BLOCK


def test_guardrails_block_forbids_specific_security_recommendations():
    assert "Never recommend a specific stock, mutual fund, or security" in GUARDRAILS_BLOCK


def test_guardrails_block_forbids_return_predictions():
    assert "Never predict returns" in GUARDRAILS_BLOCK


def test_guardrails_block_redirects_out_of_scope_questions():
    assert "tax filing specifics, legal advice, insurance underwriting" in GUARDRAILS_BLOCK


def test_guardrails_block_handles_financial_distress_supportively():
    assert "financial distress" in GUARDRAILS_BLOCK
    assert "never with product or investment suggestions" in GUARDRAILS_BLOCK


def test_advice_panel_and_fino_share_the_same_guardrail_text():
    fino_prompt = build_fino_system_prompt({}, {"screens": []})
    assert GUARDRAILS_BLOCK in fino_prompt
    assert GUARDRAILS_BLOCK in ADVICE_PANEL_PROMPT


def test_fino_prompt_embeds_financial_context_and_capabilities():
    context = {"latest_month": "2026-07", "active_goals": [{"name": "Emergency fund"}]}
    capabilities = {"screens": [{"route": "/goals", "label": "Goals"}]}

    prompt = build_fino_system_prompt(context, capabilities)

    assert "Emergency fund" in prompt
    assert "/goals" in prompt


def test_fino_prompt_includes_older_turns_summary_when_given():
    prompt = build_fino_system_prompt({}, {"screens": []}, older_turns_summary="the user asked about budgeting")
    assert "the user asked about budgeting" in prompt


def test_fino_prompt_omits_recap_section_when_no_summary():
    prompt = build_fino_system_prompt({}, {"screens": []})
    assert "Earlier in this conversation" not in prompt


def test_fino_never_claims_to_be_a_registered_adviser():
    assert "never claim to be a SEBI-registered adviser" in GUARDRAILS_BLOCK
