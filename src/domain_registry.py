DOMAIN_REGISTRY = {
    "transactional_sales_dataset": {
        "display_name": "Retail Sales",
        "supported": True,
        "detection_keywords": [
            "order",
            "invoice",
            "transaction"
        ],
        "health_sections": [
            {"key": "sales", "label": "Sales"},
            {"key": "profitability", "label": "Profitability"},
            {"key": "customers", "label": "Customers"},
            {"key": "data_quality", "label": "Data Quality"}
        ],
        "supported_analyses": [
            "sales_by_geography",
            "profitability_by_geography",
            "sales_over_time",
            "profitability_over_time",
            "sales_by_customer_segment",
            "profitability_by_customer_segment",
            "sales_by_product_category",
            "profitability_by_product_category",
            "discount_vs_profitability",
            "quantity_by_product_category"
        ],
        "extension_points": {
            "findings": [],
            "recommendations": []
        }
    },
    "customer_dataset": {
        "display_name": "Customer Management",
        "supported": True,
        "detection_keywords": [
            "customer",
            "client",
            "consumer"
        ],
        "health_sections": [
            {"key": "customers", "label": "Customers"},
            {"key": "sales", "label": "Sales"},
            {"key": "profitability", "label": "Profitability"},
            {"key": "data_quality", "label": "Data Quality"}
        ],
        "supported_analyses": [
            "sales_by_customer_segment",
            "profitability_by_customer_segment"
        ],
        "extension_points": {
            "findings": [],
            "recommendations": []
        }
    },
    "product_dataset": {
        "display_name": "Product Management",
        "supported": True,
        "detection_keywords": [
            "product",
            "item",
            "sku",
            "category",
            "subcategory"
        ],
        "health_sections": [
            {"key": "sales", "label": "Sales"},
            {"key": "profitability", "label": "Profitability"},
            {"key": "data_quality", "label": "Data Quality"}
        ],
        "supported_analyses": [
            "sales_by_product_category",
            "profitability_by_product_category",
            "quantity_by_product_category"
        ],
        "extension_points": {
            "findings": [],
            "recommendations": []
        }
    },
    "financial_or_sales_dataset": {
        "display_name": "Finance / Sales",
        "supported": True,
        "detection_keywords": [
            "sales",
            "sale",
            "revenue",
            "profit",
            "margin",
            "cost",
            "expense",
            "expenses",
            "price",
            "amount"
        ],
        "health_sections": [
            {"key": "sales", "label": "Revenue"},
            {"key": "profitability", "label": "Profitability"},
            {"key": "data_quality", "label": "Data Quality"}
        ],
        "supported_analyses": [
            "sales_by_geography",
            "profitability_by_geography",
            "sales_over_time",
            "profitability_over_time",
            "discount_vs_profitability"
        ],
        "extension_points": {
            "findings": [],
            "recommendations": []
        }
    },
    "general_business_dataset": {
        "display_name": "General Business",
        "supported": True,
        "detection_keywords": [],
        "health_sections": [
            {"key": "sales", "label": "Sales"},
            {"key": "profitability", "label": "Profitability"},
            {"key": "customers", "label": "Customers"},
            {"key": "data_quality", "label": "Data Quality"}
        ],
        "supported_analyses": [
            "sales_by_geography",
            "profitability_by_geography",
            "sales_over_time",
            "profitability_over_time",
            "sales_by_customer_segment",
            "profitability_by_customer_segment",
            "sales_by_product_category",
            "profitability_by_product_category",
            "discount_vs_profitability",
            "quantity_by_product_category"
        ],
        "extension_points": {
            "findings": [],
            "recommendations": []
        }
    },
    "healthcare_dataset": {
        "display_name": "Healthcare",
        "supported": False,
        "detection_keywords": [
            "patient",
            "diagnosis",
            "treatment",
            "clinical",
            "hospital"
        ],
        "health_sections": [
            {"key": "patients", "label": "Patients"},
            {"key": "treatments", "label": "Treatments"},
            {"key": "costs", "label": "Costs"},
            {"key": "data_quality", "label": "Data Quality"}
        ],
        "supported_analyses": []
    },
    "hr_dataset": {
        "display_name": "Human Resources",
        "supported": False,
        "detection_keywords": [
            "employee",
            "salary",
            "compensation",
            "performance"
        ],
        "health_sections": [
            {"key": "employees", "label": "Employees"},
            {"key": "performance", "label": "Performance"},
            {"key": "compensation", "label": "Compensation"},
            {"key": "data_quality", "label": "Data Quality"}
        ],
        "supported_analyses": []
    },
    "crypto_dataset": {
        "display_name": "Financial Markets / Cryptocurrency",
        "supported": False,
        "detection_keywords": [
            "crypto",
            "bitcoin",
            "ethereum",
            "token",
            "coin",
            "volume",
            "market cap"
        ],
        "health_sections": [
            {"key": "price", "label": "Price"},
            {"key": "volume", "label": "Volume"},
            {"key": "volatility", "label": "Volatility"},
            {"key": "data_quality", "label": "Data Quality"}
        ],
        "supported_analyses": []
    },
    "limited_business_dataset": {
        "display_name": "Limited Business Context",
        "supported": False,
        "detection_keywords": [],
        "health_sections": [],
        "supported_analyses": []
    }
}


def get_domain_config(dataset_type):
    return DOMAIN_REGISTRY.get(
        dataset_type,
        DOMAIN_REGISTRY["limited_business_dataset"]
    )


def get_domain_display_name(dataset_type):
    return get_domain_config(dataset_type).get(
        "display_name",
        "Limited Business Context"
    )


def is_supported_domain(dataset_type):
    return bool(get_domain_config(dataset_type).get("supported"))


def get_supported_analysis_ids(dataset_type):
    return get_domain_config(dataset_type).get("supported_analyses", [])


def get_health_sections(dataset_type):
    return get_domain_config(dataset_type).get("health_sections", [])


def get_domain_detection_keywords(dataset_type):
    return get_domain_config(dataset_type).get("detection_keywords", [])
