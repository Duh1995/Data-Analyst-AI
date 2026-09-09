import unittest

from app import get_overview_kpis


class OverviewKpiTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
