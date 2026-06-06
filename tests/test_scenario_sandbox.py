import pandas as pd

from modules.scenario_sandbox import ScenarioSandbox


def test_stress_test_portfolio_uses_predefined_scenarios():
    sandbox = ScenarioSandbox()
    portfolio = pd.DataFrame(
        [
            {"Symbol": "AAPL", "Shares": 2, "Current_Price": 100.0, "Value": 200.0, "Weight": 0.5},
            {"Symbol": "THYAO", "Shares": 1, "Current_Price": 300.0, "Value": 300.0, "Weight": 0.5},
        ]
    )

    results = sandbox.stress_test_portfolio(portfolio, scenarios=["tcmb_hike_500bp"])

    assert "tcmb_hike_500bp" in results
    assert "portfolio_change_pct" in results["tcmb_hike_500bp"]
