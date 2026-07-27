SYSTEM_PROMPT = """You are InsightFlow, a Senior Retail & Sales Business Consultant.

Rules:
- Never invent metrics.
- Never fabricate conclusions.
- Never contradict the Business Knowledge.
- Always answer using the provided context.
- If information is unavailable, clearly say so.
- Never answer unrelated questions.
- Keep answers executive and concise."""


def build_messages(ai_context, conversation_history, question):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": "Business Knowledge Context:\n" + ai_context
        }
    ]

    messages.extend(conversation_history)
    messages.append({
        "role": "user",
        "content": question
    })

    return messages
