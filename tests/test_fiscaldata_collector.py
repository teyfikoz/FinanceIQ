from app.data_collectors.fiscaldata import FiscalDataCollector


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_fiscaldata_collector_builds_official_indicator_snapshot(monkeypatch):
    collector = FiscalDataCollector()

    def _fake_request(url, params=None, headers=None, timeout=30):
        if "debt_to_penny" in url:
            return _FakeResponse(
                {
                    "data": [
                        {
                            "record_date": "2026-06-05",
                            "tot_pub_debt_out_amt": "36500000000000.00",
                            "debt_held_public_amt": "28750000000000.00",
                            "intragov_hold_amt": "7750000000000.00",
                        },
                        {
                            "record_date": "2026-06-04",
                            "tot_pub_debt_out_amt": "36480000000000.00",
                            "debt_held_public_amt": "28720000000000.00",
                            "intragov_hold_amt": "7760000000000.00",
                        },
                    ]
                }
            )
        if "operating_cash_balance" in url:
            return _FakeResponse(
                {
                    "data": [
                        {
                            "record_date": "2026-06-05",
                            "account_type": "Treasury General Account (TGA)",
                            "open_today_bal": "645321",
                            "close_today_bal": "612345",
                        },
                        {
                            "record_date": "2026-06-04",
                            "account_type": "Treasury General Account (TGA)",
                            "open_today_bal": "671000",
                            "close_today_bal": "645321",
                        },
                    ]
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(collector, "_make_request", _fake_request)

    payload = collector.get_fiscal_indicators()
    indicators = payload["fiscal_indicators"]

    assert "tot_pub_debt_out_amt" in indicators
    assert indicators["tot_pub_debt_out_amt"]["name"] == "US Public Debt"
    assert indicators["tot_pub_debt_out_amt"]["display_value"] == 36500000000000.0
    assert "debt_held_public_amt" in indicators
    assert "tga_closing_balance" in indicators
    assert indicators["tga_closing_balance"]["display_value"] == 612345000000.0
    assert indicators["tga_closing_balance"]["source_dataset"] == "Daily Treasury Statement"
