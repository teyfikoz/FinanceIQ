import pandas as pd

from modules.portfolio_health import PortfolioHealthScore


class _FakeTicker:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.info = {"sector": "Technology", "beta": 1.1, "marketCap": 10_000_000, "averageVolume": 1_000_000}

    def history(self, period: str = "6mo"):
        if self.symbol in {"AAPL", "THYAO.IS"}:
            return pd.DataFrame({"Close": [100, 101, 102], "Volume": [1000, 1100, 1200]})
        return pd.DataFrame()


def test_resolve_market_data_prefers_native_then_bist_suffix(monkeypatch):
    monkeypatch.setattr("modules.portfolio_health.yf.Ticker", _FakeTicker)

    engine = PortfolioHealthScore()
    resolved_aapl, *_ = engine._resolve_market_data("AAPL")
    resolved_thyao, *_ = engine._resolve_market_data("THYAO")

    assert resolved_aapl == "AAPL"
    assert resolved_thyao == "THYAO.IS"
