import re

from src.ai.providers.base_provider import AIProvider


UNAVAILABLE_MESSAGE = (
    "That information is not present in the current Business Knowledge. "
    "InsightFlow cannot answer it without deterministic business evidence."
)

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10
}


class MockProvider(AIProvider):
    def generate_response(self, messages):
        context = self.get_context(messages)
        question = self.get_question(messages)
        sections = self.parse_sections(context)

        if not context or not question:
            return UNAVAILABLE_MESSAGE

        normalized_question = question.lower()

        if self.is_summary_question(normalized_question):
            return self.summarize_business(sections)

        if "biggest risk" in normalized_question or "main risk" in normalized_question:
            return self.find_biggest_risk(sections)

        if (
            "biggest opportunity" in normalized_question
            or "main opportunity" in normalized_question
        ):
            return self.find_biggest_opportunity(sections)

        if "recommendation" in normalized_question and "explain" in normalized_question:
            return self.explain_numbered_item(
                sections.get("Recommendations", []),
                self.extract_requested_number(normalized_question),
                "recommendation"
            )

        if "insight" in normalized_question and "explain" in normalized_question:
            return self.explain_numbered_item(
                sections.get("Business Insights", []),
                self.extract_requested_number(normalized_question),
                "insight"
            )

        if "region" in normalized_question and "performs best" in normalized_question:
            return self.find_performance_answer(
                sections,
                ["region", "market", "geography"],
                "region"
            )

        if (
            "product category" in normalized_question
            and "performs best" in normalized_question
        ):
            return self.find_performance_answer(
                sections,
                ["product category", "product"],
                "product category"
            )

        if (
            "customer segment" in normalized_question
            and "performs best" in normalized_question
        ):
            return self.find_performance_answer(
                sections,
                ["customer segment", "segment", "customer"],
                "customer segment"
            )

        if normalized_question.strip() in ["why?", "why"]:
            return self.explain_latest_context(messages)

        return UNAVAILABLE_MESSAGE

    def get_context(self, messages):
        for message in messages:
            content = message.get("content", "")

            if content.startswith("Business Knowledge Context:"):
                return content.replace("Business Knowledge Context:", "", 1).strip()

        return ""

    def get_question(self, messages):
        for message in reversed(messages):
            if message.get("role") == "user":
                content = message.get("content", "")

                if not content.startswith("Business Knowledge Context:"):
                    return content

        return ""

    def parse_sections(self, context):
        sections = {}
        current_section = None

        for raw_line in context.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            if line.endswith(":") and not line.startswith("-"):
                current_section = line[:-1]
                sections[current_section] = []
                continue

            if current_section:
                sections[current_section].append(line.lstrip("- ").strip())

        return sections

    def is_summary_question(self, question):
        return any(
            phrase in question
            for phrase in [
                "summarize my business",
                "summarise my business",
                "business summary",
                "executive summary"
            ]
        )

    def summarize_business(self, sections):
        summary_lines = sections.get("Executive Summary", [])

        if not summary_lines or summary_lines == ["Unavailable."]:
            return UNAVAILABLE_MESSAGE

        health_lines = sections.get("Business Health", [])
        priority_lines = sections.get("Executive Priorities", [])
        response_parts = ["Executive summary: " + " ".join(summary_lines)]

        if health_lines and health_lines != ["Unavailable."]:
            response_parts.append("Health: " + " ".join(health_lines[:2]))

        if priority_lines and priority_lines != ["Unavailable."]:
            response_parts.append("Top priority: " + priority_lines[0])

        return " ".join(response_parts)

    def find_biggest_risk(self, sections):
        for line in sections.get("Business Health", []):
            if "attention" in line.lower():
                return "Biggest risk: " + line

        for line in sections.get("Business Insights", []):
            if "risk" in line.lower() or "underperform" in line.lower():
                return "Biggest risk: " + line

        return UNAVAILABLE_MESSAGE

    def find_biggest_opportunity(self, sections):
        for line in sections.get("Business Insights", []):
            if "opportunity" in line.lower() or "strongest" in line.lower():
                return "Biggest opportunity: " + line

        for line in sections.get("Recommendations", []):
            if "opportunity" in line.lower() or "prioritize" in line.lower():
                return "Biggest opportunity: " + line

        return UNAVAILABLE_MESSAGE

    def explain_numbered_item(self, lines, requested_number, item_name):
        if not lines or lines == ["Unavailable."]:
            return UNAVAILABLE_MESSAGE

        index = (requested_number or 1) - 1

        if index < 0 or index >= len(lines):
            return f"That {item_name} is not present in the current Business Knowledge."

        return f"{item_name.title()} {index + 1}: {lines[index]}"

    def extract_requested_number(self, question):
        match = re.search(r"\b(\d+)\b", question)

        if match:
            return int(match.group(1))

        for word, number in NUMBER_WORDS.items():
            if re.search(rf"\b{word}\b", question):
                return number

        return None

    def find_performance_answer(self, sections, keywords, label):
        lines = (
            sections.get("Business Insights", [])
            + sections.get("Recommendations", [])
            + sections.get("Key Metrics", [])
        )

        for line in lines:
            normalized_line = line.lower()

            if any(keyword in normalized_line for keyword in keywords):
                return f"Best-performing {label}: {line}"

        return UNAVAILABLE_MESSAGE

    def explain_latest_context(self, messages):
        for message in reversed(messages[:-1]):
            if message.get("role") == "assistant":
                return (
                    "Because the previous answer was based only on this "
                    "deterministic Business Knowledge item: "
                    + message.get("content", "")
                )

        return UNAVAILABLE_MESSAGE
