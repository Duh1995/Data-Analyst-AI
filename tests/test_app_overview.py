import unittest

from app import (
    BUSINESS_AREA_CONFIG,
    get_overview_kpis,
    get_sales_analyses,
    get_sales_kpis
)
from src.analysis_catalog import get_analysis_catalog


class OverviewKpiTests(unittest.TestCase):
    def test_business_area_navigation_has_shared_page_configuration(self):
        self.assertEqual(
            list(BUSINESS_AREA_CONFIG),
            ["Sales", "Profitability", "Customers", "Products"]
        )
        for config in BUSINESS_AREA_CONFIG.values():
            self.assertTrue(config["description"])

    def test_overview_uses_available_business_metrics(self):
        profile = {
            "rows": 12,
            "business_metrics": {
                "sales": {
                    "metrics_by_column": {
                        "Revenue": {"total": 1250.5}
                    }
                },
                "profitability": {
                    "metrics_by_column": {
                        "Profit": {"total": 320}
                    }
                },
                "customers": {
                    "unique_counts": {"Customer ID": 8}
                }
            }
        }

        self.assertEqual(
            get_overview_kpis(profile),
            [
                {"label": "Sales", "value": "1,250.50", "context": "Revenue"},
                {"label": "Profit", "value": "320", "context": "Profit"},
                {"label": "Customers", "value": "8", "context": "Customer ID"},
                {"label": "Records", "value": "12", "context": "Dataset"}
            ]
        )

    def test_overview_falls_back_gracefully_for_incomplete_data(self):
        profile = {
            "rows": 3,
            "business_metrics": {
                "sales": {"metrics_by_column": {}}
            }
        }

        self.assertEqual(
            get_overview_kpis(profile),
            [{"label": "Records", "value": "3", "context": "Dataset"}]
        )

    def test_sales_kpis_use_deterministic_values_and_adaptive_fallbacks(self):
        profile = {
            "rows": 10,
            "business_metrics": {
                "sales": {
                    "metrics_by_column": {
                        "Revenue": {"total": 1000, "count": 10}
                    }
                }
            }
        }

        self.assertEqual(
            get_sales_kpis(profile),
            [
                {"label": "Revenue", "value": "1,000", "supporting_text": "Revenue"},
                {"label": "Sales records", "value": "10", "supporting_text": "Revenue"},
                {"label": "Records", "value": "10", "supporting_text": "Dataset"}
            ]
        )

    def test_sales_analysis_selection_uses_only_available_priority_items(self):
        available = [
            {
                "id": "sales_over_time",
                "available": True,
                "matched_concepts": {"metrics": {}, "dimensions": {}}
            },
            {
                "id": "sales_by_geography",
                "available": False,
                "matched_concepts": {"metrics": {}, "dimensions": {}}
            }
        ]

        selected = get_sales_analyses(available, get_analysis_catalog())
        self.assertEqual([analysis["id"] for analysis in selected], ["sales_over_time"])


if __name__ == "__main__":
    unittest.main()
