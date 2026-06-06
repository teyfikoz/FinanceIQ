import pandas as pd

from modules.etf_weight_tracker import ETFWeightTracker


class _FakeFundsData:
    def __init__(self):
        self.top_holdings = pd.DataFrame(
            {
                "Name": ["Apple Inc.", "Microsoft Corp."],
                "Holding Percent": [0.082, 0.071],
            },
            index=pd.Index(["AAPL", "MSFT"], name="Symbol"),
        )


def test_normalize_holdings_frame_supports_funds_data(tmp_path):
    tracker = ETFWeightTracker(db_path=str(tmp_path / "holdings.db"))

    df = tracker._normalize_holdings_frame(_FakeFundsData(), "SPY")

    assert not df.empty
    assert list(df["stock_symbol"]) == ["AAPL", "MSFT"]
    assert list(df["fund_code"].unique()) == ["SPY"]
    assert round(float(df.iloc[0]["weight_pct"]), 1) == 8.2
