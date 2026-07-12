ANALYSIS_CATALOG = [
    {
        "id": "sales_by_geography",
        "title": "Sales by Geography",
        "required_concepts": {
            "metrics": ["sales"],
            "dimensions": ["geography"]
        },
        "business_question": "Which geographic areas generate the highest sales?",
        "decision_supported": "Compare commercial performance across markets.",
        "business_value": "high",
        "complexity": "basic",
        "prerequisites": [
            "At least one sales metric is available.",
            "At least one geographic dimension is available."
        ],
        "preferred_chart": "bar"
    },
    {
        "id": "profitability_by_geography",
        "title": "Profitability by Geography",
        "required_concepts": {
            "metrics": ["profitability"],
            "dimensions": ["geography"]
        },
        "business_question": "Which geographic areas generate the highest profitability?",
        "decision_supported": "Compare profitability across markets.",
        "business_value": "high",
        "complexity": "basic",
        "prerequisites": [
            "At least one profitability metric is available.",
            "At least one geographic dimension is available."
        ],
        "preferred_chart": "bar"
    },
    {
        "id": "sales_over_time",
        "title": "Sales Over Time",
        "required_concepts": {
            "metrics": ["sales"],
            "dimensions": ["time"]
        },
        "business_question": "How do sales evolve over time?",
        "decision_supported": "Monitor commercial performance trends.",
        "business_value": "high",
        "complexity": "basic",
        "prerequisites": [
            "At least one sales metric is available.",
            "A time dimension is available."
        ],
        "preferred_chart": "line"
    },
    {
        "id": "profitability_over_time",
        "title": "Profitability Over Time",
        "required_concepts": {
            "metrics": ["profitability"],
            "dimensions": ["time"]
        },
        "business_question": "How does profitability evolve over time?",
        "decision_supported": "Monitor profitability trends.",
        "business_value": "high",
        "complexity": "basic",
        "prerequisites": [
            "At least one profitability metric is available.",
            "A time dimension is available."
        ],
        "preferred_chart": "line"
    },
    {
        "id": "sales_by_customer_segment",
        "title": "Sales by Customer Segment",
        "required_concepts": {
            "metrics": ["sales"],
            "dimensions": ["customer_segment"]
        },
        "business_question": "Which customer segments generate the highest sales?",
        "decision_supported": "Compare commercial performance across customer groups.",
        "business_value": "medium",
        "complexity": "basic",
        "prerequisites": [
            "At least one sales metric is available.",
            "A customer segment dimension is available."
        ],
        "preferred_chart": "bar"
    },
    {
        "id": "profitability_by_customer_segment",
        "title": "Profitability by Customer Segment",
        "required_concepts": {
            "metrics": ["profitability"],
            "dimensions": ["customer_segment"]
        },
        "business_question": "Which customer segments generate the highest profitability?",
        "decision_supported": "Compare profitability across customer groups.",
        "business_value": "medium",
        "complexity": "basic",
        "prerequisites": [
            "At least one profitability metric is available.",
            "A customer segment dimension is available."
        ],
        "preferred_chart": "bar"
    },
    {
        "id": "sales_by_product_category",
        "title": "Sales by Product Category",
        "required_concepts": {
            "metrics": ["sales"],
            "dimensions": ["product_category"]
        },
        "business_question": "Which product categories generate the highest sales?",
        "decision_supported": "Compare commercial performance across product groups.",
        "business_value": "high",
        "complexity": "basic",
        "prerequisites": [
            "At least one sales metric is available.",
            "A product category dimension is available."
        ],
        "preferred_chart": "bar"
    },
    {
        "id": "profitability_by_product_category",
        "title": "Profitability by Product Category",
        "required_concepts": {
            "metrics": ["profitability"],
            "dimensions": ["product_category"]
        },
        "business_question": "Which product categories generate the highest profitability?",
        "decision_supported": "Compare profitability across product groups.",
        "business_value": "high",
        "complexity": "basic",
        "prerequisites": [
            "At least one profitability metric is available.",
            "A product category dimension is available."
        ],
        "preferred_chart": "bar"
    },
    {
        "id": "discount_vs_profitability",
        "title": "Discount vs Profitability",
        "required_concepts": {
            "metrics": ["discount", "profitability"],
            "dimensions": []
        },
        "business_question": "How does discount relate to profitability?",
        "decision_supported": "Understand the relationship between discounting and profitability.",
        "business_value": "medium",
        "complexity": "intermediate",
        "prerequisites": [
            "At least one discount metric is available.",
            "At least one profitability metric is available."
        ],
        "preferred_chart": "scatter"
    },
    {
        "id": "quantity_by_product_category",
        "title": "Quantity by Product Category",
        "required_concepts": {
            "metrics": ["quantity"],
            "dimensions": ["product_category"]
        },
        "business_question": "Which product categories have the highest quantity sold?",
        "decision_supported": "Compare sales volume across product groups.",
        "business_value": "medium",
        "complexity": "basic",
        "prerequisites": [
            "At least one quantity metric is available.",
            "A product category dimension is available."
        ],
        "preferred_chart": "bar"
    }
]


def get_analysis_catalog():
    return [
        analysis.copy()
        for analysis in ANALYSIS_CATALOG
    ]
