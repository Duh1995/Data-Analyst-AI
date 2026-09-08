import re

from src.ai.providers.base_provider import AIProvider


UNAVAILABLE_MESSAGE = (
    "Answer\n"
    "That information is not present in the current Business Knowledge.\n\n"
    "Supporting Evidence\n"
    "No deterministic business evidence was found for this question.\n\n"
    "Business Context\n"
    "InsightFlow only answers from the Business Knowledge context.\n\n"
    "Recommended Action\n"
    "Review the available Business Health, Insights, Recommendations and "
    "Executive Priorities."
)

UNRELATED_MESSAGE = (
    "Answer\n"
    "I can only answer business questions about the current dataset.\n\n"
    "Supporting Evidence\n"
    "The question does not match a supported Business Knowledge intent.\n\n"
    "Business Context\n"
    "InsightFlow does not answer unrelated questions, invent metrics or analyse "
    "raw data.\n\n"
    "Recommended Action\n"
    "Ask about business summary, health, risks, opportunities, priorities, "
    "recommendations, insights or performance."
)

UNSUPPORTED_DOMAIN_MESSAGE = (
    "Answer\n"
    "Conversational business guidance is currently available only for Retail & "
    "Sales datasets.\n\n"
    "Supporting Evidence\n"
    "The current Business Knowledge does not contain supported Retail & Sales "
    "guidance.\n\n"
    "Business Context\n"
    "InsightFlow will not fabricate advice for unsupported domains.\n\n"
    "Recommended Action\n"
    "Use the dataset profile and charts, or upload a Retail & Sales dataset for "
    "business copilot guidance."
)

CHART_UNAVAILABLE_MESSAGE = (
    "Answer\n"
    "Chart interpretation is unavailable because no current chart context is "
    "present in the Business Knowledge.\n\n"
    "Supporting Evidence\n"
    "The Business Knowledge context does not identify the selected analysis or "
    "chart decision context.\n\n"
    "Business Context\n"
    "InsightFlow only explains chart purpose when the selected analysis is known.\n\n"
    "Recommended Action\n"
    "Use the visible chart title and Executive Priorities to choose the business "
    "analysis to discuss."
)

SUPPORTED_DATASET_TYPES = {
    "transactional_sales_dataset",
    "financial_or_sales_dataset",
    "customer_dataset",
    "product_dataset",
    "general_business_dataset"
}

FOLLOW_UP_QUESTIONS = {
    "why",
    "why?",
    "explain that",
    "tell me more",
    "why is that important",
    "why is that important?",
    "what do you mean",
    "what do you mean?"
}

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

INTENT_RULES = [
    ("business_summary", ["summarize my business", "summarise my business", "business summary", "executive summary", "summarize"]),
    ("business_health", ["business health", "health", "healthy"]),
    ("executive_priorities", ["executive priorities", "priorities", "priority"]),
    ("biggest_risk", ["biggest risk", "main risk", "risk"]),
    ("biggest_opportunity", ["biggest opportunity", "main opportunity", "opportunity"]),
    ("explain_insight", ["explain insight", "insight"]),
    ("explain_recommendation", ["explain recommendation", "recommendation"]),
    ("profitability", ["profitability", "profit", "margin"]),
    ("sales_performance", ["sales performance", "sales", "revenue"]),
    ("regional_performance", ["region", "regional", "market", "geography"]),
    ("product_category_performance", ["product category", "category", "product"]),
    ("customer_segment_performance", ["customer segment", "segment", "customer"]),
    ("discount_impact", ["discount impact", "discount"]),
    ("explain_current_chart", ["current chart", "this chart", "chart"]),
    ("compare_business_areas", ["compare"]),
    ("strategic_advice", ["strategic advice", "strategy", "what should i do", "what should management focus", "what should i do first"])
]


class MockProvider(AIProvider):
    def generate_response(self, messages):
        context = self.get_context(messages)
        question = self.get_question(messages)

        if not context or not question:
            return UNAVAILABLE_MESSAGE

        business_knowledge = self.parse_business_knowledge(context)

        if not self.is_supported_business_knowledge(business_knowledge):
            return UNSUPPORTED_DOMAIN_MESSAGE

        intent = self.detect_intent(question)
        active_question = question

        if intent == "follow_up":
            previous_question = self.get_previous_question(messages)
            active_question = previous_question
            intent = self.detect_intent(previous_question)

        if intent == "business_summary":
            return self.build_business_summary_response(business_knowledge)

        if intent == "business_health":
            return self.build_business_health_response(business_knowledge)

        if intent == "executive_priorities":
            return self.build_priorities_response(business_knowledge)

        if intent == "biggest_risk":
            return self.build_risk_response(business_knowledge)

        if intent == "biggest_opportunity":
            return self.build_opportunity_response(business_knowledge)

        if intent == "explain_insight":
            return self.build_numbered_response(
                business_knowledge,
                "Business Insights",
                self.extract_requested_number(active_question),
                "insight"
            )

        if intent == "explain_recommendation":
            return self.build_numbered_response(
                business_knowledge,
                "Recommendations",
                self.extract_requested_number(active_question),
                "recommendation"
            )

        if intent == "profitability":
            return self.build_topic_response(
                business_knowledge,
                "profitability",
                ["profit", "profitability", "margin"]
            )

        if intent == "sales_performance":
            return self.build_topic_response(
                business_knowledge,
                "sales performance",
                ["sales", "revenue"]
            )

        if intent == "regional_performance":
            return self.build_topic_response(
                business_knowledge,
                "regional performance",
                ["primary revenue driver", "strongest market", "revenue concentration"]
            )

        if intent == "product_category_performance":
            return self.build_topic_response(
                business_knowledge,
                "product category performance",
                ["product", "category", "subcategory"]
            )

        if intent == "customer_segment_performance":
            return self.build_topic_response(
                business_knowledge,
                "customer segment performance",
                ["customer", "segment", "consumer", "client"]
            )

        if intent == "discount_impact":
            return self.build_topic_response(
                business_knowledge,
                "discount impact",
                ["discount"]
            )

        if intent == "explain_current_chart":
            return CHART_UNAVAILABLE_MESSAGE

        if intent == "compare_business_areas":
            return self.build_comparison_response(business_knowledge, active_question)

        if intent == "strategic_advice":
            return self.build_strategic_advice_response(business_knowledge)

        return UNRELATED_MESSAGE

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

    def get_previous_question(self, messages):
        current_question_seen = False

        for message in reversed(messages):
            if message.get("role") != "user":
                continue

            content = message.get("content", "")

            if content.startswith("Business Knowledge Context:"):
                continue

            if not current_question_seen:
                current_question_seen = True
                continue

            return content

        return ""

    def parse_business_knowledge(self, context):
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

    def detect_intent(self, question):
        normalized_question = self.normalize_text(question)

        if normalized_question in FOLLOW_UP_QUESTIONS:
            return "follow_up"

        for intent, phrases in INTENT_RULES:
            if any(phrase in normalized_question for phrase in phrases):
                return intent

        return "unknown"

    def normalize_text(self, value):
        return re.sub(r"\s+", " ", str(value).lower()).strip()

    def is_supported_business_knowledge(self, business_knowledge):
        summary_lines = business_knowledge.get("Executive Summary", [])
        dataset_type = self.find_prefixed_value(summary_lines, "Dataset type:")

        return dataset_type in SUPPORTED_DATASET_TYPES

    def find_prefixed_value(self, lines, prefix):
        for line in lines:
            if line.startswith(prefix):
                return line.replace(prefix, "", 1).strip()

        return ""

    def get_available_lines(self, business_knowledge, section_name):
        lines = business_knowledge.get(section_name, [])

        if not lines or lines == ["Unavailable."]:
            return []

        return lines

    def build_response(self, answer, evidence=None, context=None, action=None):
        parts = [
            "Answer\n" + answer,
            "Supporting Evidence\n" + self.join_lines(evidence),
            "Business Context\n" + (context or "This answer uses only Business Knowledge.")
        ]

        if action:
            parts.append("Recommended Action\n" + action)

        return "\n\n".join(parts)

    def join_lines(self, lines):
        clean_lines = self.unique_lines(lines or [])

        if not clean_lines:
            return "No supporting evidence is available in Business Knowledge."

        return "\n".join(f"- {line}" for line in clean_lines[:3])

    def unique_lines(self, lines):
        seen = set()
        unique = []

        for line in lines:
            normalized_line = self.normalize_text(line)

            if normalized_line in seen:
                continue

            seen.add(normalized_line)
            unique.append(line)

        return unique

    def build_business_summary_response(self, business_knowledge):
        summary = self.get_available_lines(business_knowledge, "Executive Summary")
        health = self.get_available_lines(business_knowledge, "Business Health")
        priorities = self.get_available_lines(business_knowledge, "Executive Priorities")

        if not summary:
            return UNAVAILABLE_MESSAGE

        answer = "The business is summarized by the available dataset type, readiness, areas and warnings."
        evidence = summary[:4] + health[:1] + priorities[:1]
        context = "This is an executive view of the current Business Knowledge."
        action = self.extract_action_from_line(priorities[0]) if priorities else None

        return self.build_response(answer, evidence, context, action)

    def build_business_health_response(self, business_knowledge):
        health = self.get_available_lines(business_knowledge, "Business Health")

        if not health:
            return UNAVAILABLE_MESSAGE

        attention_lines = self.find_lines(health, ["attention"])
        answer = (
            "Business Health has areas requiring attention."
            if attention_lines
            else "Business Health does not show attention flags in the available evidence."
        )
        evidence = attention_lines or health
        context = "Health is based on the Business Health section only."

        return self.build_response(answer, evidence, context)

    def build_priorities_response(self, business_knowledge):
        priorities = self.get_available_lines(business_knowledge, "Executive Priorities")

        if not priorities:
            return UNAVAILABLE_MESSAGE

        return self.build_response(
            "The first executive priority is the recommended place to focus.",
            priorities[:3],
            "Priorities are ranked by the deterministic Business Knowledge pipeline.",
            self.extract_action_from_line(priorities[0])
        )

    def build_risk_response(self, business_knowledge):
        health = self.get_available_lines(business_knowledge, "Business Health")
        insights = self.get_available_lines(business_knowledge, "Business Insights")
        evidence = (
            self.find_lines(insights, ["risk", "underperform", "behind", "lower"])
            + self.find_lines(health, ["attention", "missing", "duplicate"])
        )

        if not evidence:
            return UNAVAILABLE_MESSAGE

        return self.build_response(
            "The biggest visible risk is the strongest risk or attention signal in Business Knowledge.",
            evidence,
            "Risk is selected from Business Health and Business Insights only.",
            self.find_recommended_action(business_knowledge, evidence)
        )

    def build_opportunity_response(self, business_knowledge):
        insights = self.get_available_lines(business_knowledge, "Business Insights")
        recommendations = self.get_available_lines(business_knowledge, "Recommendations")
        evidence = (
            self.find_lines(insights, ["opportunity", "strongest", "growth", "driver"])
            + self.find_lines(recommendations, ["opportunity", "prioritize", "investment", "growth"])
        )

        if not evidence:
            return UNAVAILABLE_MESSAGE

        return self.build_response(
            "The biggest visible opportunity is the strongest opportunity signal in Business Knowledge.",
            evidence,
            "Opportunity is selected from deterministic insights and recommendations only.",
            self.find_recommended_action(business_knowledge, evidence)
        )

    def build_numbered_response(self, business_knowledge, section_name, requested_number, item_name):
        lines = self.get_available_lines(business_knowledge, section_name)

        if not lines:
            return UNAVAILABLE_MESSAGE

        index = (requested_number or 1) - 1

        if index < 0 or index >= len(lines):
            return self.build_response(
                f"That {item_name} is not present in the current Business Knowledge.",
                [],
                f"The {section_name} section has {len(lines)} available item(s)."
            )

        selected_line = lines[index]

        return self.build_response(
            f"{item_name.title()} {index + 1} is available in Business Knowledge.",
            [selected_line],
            f"This explanation uses item {index + 1} from {section_name}.",
            self.find_matching_recommendation(business_knowledge, selected_line)
        )

    def build_topic_response(self, business_knowledge, topic_label, keywords):
        searchable_lines = self.get_searchable_business_lines(business_knowledge)
        evidence = self.find_lines(searchable_lines, keywords)

        if not evidence:
            return UNAVAILABLE_MESSAGE

        return self.build_response(
            f"The available Business Knowledge contains evidence about {topic_label}.",
            evidence,
            f"{topic_label.title()} is interpreted only from Business Knowledge.",
            self.find_recommended_action(business_knowledge, evidence)
        )

    def build_comparison_response(self, business_knowledge, question):
        comparison_terms = self.extract_comparison_terms(question)

        if len(comparison_terms) < 2:
            return self.build_response(
                "I could not identify two business areas to compare.",
                [],
                "Comparisons require two named regions, product categories or customer segments."
            )

        searchable_lines = self.get_searchable_business_lines(business_knowledge)
        evidence = []

        for term in comparison_terms[:2]:
            term_lines = self.find_lines(searchable_lines, [term])

            if not term_lines:
                return self.build_response(
                    f"Business Knowledge does not contain comparison evidence for {term}.",
                    [],
                    "InsightFlow will not invent comparisons that are not present in Business Knowledge."
                )

            evidence.extend(term_lines[:2])

        return self.build_response(
            f"Business Knowledge contains evidence for {comparison_terms[0]} and {comparison_terms[1]}, but no new comparison is calculated.",
            evidence,
            "This comparison cites existing Business Knowledge only; it does not compute new KPIs."
        )

    def build_strategic_advice_response(self, business_knowledge):
        priorities = self.get_available_lines(business_knowledge, "Executive Priorities")
        action_plan = self.get_available_lines(
            business_knowledge,
            "Executive Action Plan"
        )
        recommendations = self.get_available_lines(business_knowledge, "Recommendations")
        insights = self.get_available_lines(business_knowledge, "Business Insights")
        evidence = (
            priorities[:2]
            + action_plan[:2]
            + recommendations[:2]
            + insights[:1]
        )

        if not evidence:
            return UNAVAILABLE_MESSAGE

        action = (
            self.extract_action_from_line(action_plan[0])
            if action_plan
            else self.extract_action_from_line(priorities[0])
            if priorities
            else self.extract_action_from_line(recommendations[0])
        )

        return self.build_response(
            "Focus first on the highest-ranked priority supported by recommendations and insights.",
            evidence,
            "Strategic advice is limited to ranked priorities, the deterministic action plan, recommendations and insights.",
            action
        )

    def get_searchable_business_lines(self, business_knowledge):
        lines = []

        for section_name in [
            "Advanced Retail Intelligence",
            "Business Health",
            "Business Insights",
            "Recommendations",
            "Executive Priorities",
            "Executive Action Plan",
            "Key Metrics"
        ]:
            lines.extend(self.get_available_lines(business_knowledge, section_name))

        return lines

    def find_lines(self, lines, keywords):
        normalized_keywords = [self.normalize_text(keyword) for keyword in keywords]

        return [
            line
            for line in lines
            if any(keyword in self.normalize_text(line) for keyword in normalized_keywords)
        ]

    def find_recommended_action(self, business_knowledge, evidence):
        recommendations = self.get_available_lines(business_knowledge, "Recommendations")

        for evidence_line in evidence or []:
            action = self.find_matching_recommendation(business_knowledge, evidence_line)

            if action:
                return action

        if recommendations:
            return self.extract_action_from_line(recommendations[0])

        return None

    def find_matching_recommendation(self, business_knowledge, selected_line):
        recommendations = self.get_available_lines(business_knowledge, "Recommendations")
        selected_text = self.normalize_text(selected_line)

        for recommendation in recommendations:
            title = recommendation.split(":", 1)[0]

            if self.normalize_text(title) and self.normalize_text(title) in selected_text:
                return self.extract_action_from_line(recommendation)

        return None

    def extract_action_from_line(self, line):
        if not line:
            return None

        if ":" in line:
            return line.split(":", 1)[1].strip()

        return line.strip()

    def extract_requested_number(self, question):
        normalized_question = self.normalize_text(question)
        match = re.search(r"\b(\d+)\b", normalized_question)

        if match:
            return int(match.group(1))

        for word, number in NUMBER_WORDS.items():
            if re.search(rf"\b{word}\b", normalized_question):
                return number

        return None

    def extract_comparison_terms(self, question):
        match = re.search(
            r"\bcompare\s+(.+?)\s+(?:and|vs|versus)\s+(.+?)(?:[?.!]|$)",
            question,
            flags=re.IGNORECASE
        )

        if not match:
            return []

        return [
            self.normalize_comparison_term(match.group(1)),
            self.normalize_comparison_term(match.group(2))
        ]

    def normalize_comparison_term(self, value):
        return re.sub(r"[^A-Za-z0-9 &_-]", "", value).strip().lower()
