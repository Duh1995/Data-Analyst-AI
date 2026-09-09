import unittest

from app import (
    BUSINESS_AREA_CONFIG,
    get_overview_kpis,
    get_profitability_analyses,
    get_profitability_kpis,
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

    def test_profitability_kpis_do_not_invent_missing_costs(self):
        profile = {
            "rows": 7,
            "business_metrics": {
                "profitability": {
                    "metrics_by_column": {
                        "Profit": {"total": 240}
                    }
                }
            }
        }

        kpis = get_profitability_kpis(profile)
        self.assertEqual(kpis[0]["label"], "Profit")
        self.assertEqual(kpis[0]["value"], "240")
        self.assertEqual(kpis[1]["label"], "Records")
        self.assertEqual(kpis[2]["value"], None)

    def test_profitability_margin_is_not_presented_as_profit(self):
        profile = {
            "rows": 4,
            "business_metrics": {
                "profitability": {
                    "metrics_by_column": {
                        "Margin": {"total": 0.24}
                    }
                }
            }
        }

        self.assertEqual(get_profitability_kpis(profile)[0]["label"], "Margin")

    def test_profitability_analysis_selection_is_limited_to_four_available_items(self):
        available = [
            {
                "id": analysis_id,
                "available": True,
                "matched_concepts": {"metrics": {}, "dimensions": {}}
            }
            for analysis_id in (
                "profitability_over_time",
                "profitability_by_product_category",
                "discount_vs_profitability",
                "profitability_by_geography",
                "profitability_by_customer_segment"
            )
        ]

        selected = get_profitability_analyses(available, get_analysis_catalog())
        self.assertEqual(len(selected), 4)
        self.assertNotIn(
            "profitability_by_customer_segment",
            [analysis["id"] for analysis in selected]
        )


if __name__ == "__main__":
    unittest.main()
