from src.ai.context_builder import build_ai_context
from src.ai.conversation_manager import ConversationManager
from src.ai.prompt_builder import build_messages
from src.ai.providers.mock_provider import MockProvider
from src.domain_registry import is_supported_domain


SELECTED_PROVIDER = MockProvider


def is_supported_business_knowledge(business_knowledge):
    dataset_type = (
        business_knowledge
        .get("summary", {})
        .get("dataset_type")
    )

    return is_supported_domain(dataset_type)


def get_suggested_questions(business_knowledge):
    if not is_supported_business_knowledge(business_knowledge):
        return []

    suggestions = []
    insight_text = " ".join(
        " ".join(
            str(insight.get(key, ""))
            for key in ["title", "finding", "impact_category", "recommendation"]
        ).lower()
        for insight in business_knowledge.get("insights", [])
    )
    health = business_knowledge.get("health", {})

    if "profit" in insight_text or "profitability" in health:
        suggestions.append("Why is profitability low?")

    if "customer" in insight_text or "customers" in health:
        suggestions.append("Which customer segment should I prioritise?")

    if any(keyword in insight_text for keyword in ["region", "market", "geography"]):
        suggestions.append("Which region deserves more investment?")

    if business_knowledge.get("recommendations"):
        suggestions.append("Explain recommendation two.")

    if business_knowledge.get("priorities"):
        suggestions.append("What should management focus on first?")

    return suggestions[:5]


def answer_question(
    question,
    profile,
    df=None,
    conversation_manager=None,
    provider=None
):
    business_knowledge = profile.get("business_knowledge", {})

    if not is_supported_business_knowledge(business_knowledge):
        return "Business AI answers are not available for this domain yet."

    conversation_manager = conversation_manager or ConversationManager()
    provider = provider or SELECTED_PROVIDER()
    ai_context = build_ai_context(business_knowledge)
    messages = build_messages(
        ai_context,
        conversation_manager.get_history(),
        question
    )
    answer = provider.generate_response(messages)

    conversation_manager.add_interaction(question, answer)

    return answer
