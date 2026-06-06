from datetime import datetime

from app.data_collectors.evds import EVDSCollector


def test_evds_collector_builds_macro_indicator_snapshot(monkeypatch):
    collector = EVDSCollector()

    def _fake_post(path, payload, timeout=30):
        assert path == "fe"
        assert payload["series"] == "TP.AB.C1-TP.AB.C2"
        return {
            "items": [
                {"Tarih": "24-05-2026", "TP_AB_C1": "81,440", "TP_AB_C2": "70,610"},
                {"Tarih": "31-05-2026", "TP_AB_C1": "82,650", "TP_AB_C2": "71,885"},
            ]
        }

    monkeypatch.setattr(collector, "_post_json", _fake_post)

    payload = collector.get_macro_indicators()
    indicators = payload["macro_indicators"]

    assert indicators["TP.AB.C1"]["name"] == "Gold Reserves"
    assert indicators["TP.AB.C1"]["display_value"] == 82650000000.0
    assert indicators["TP.AB.C2"]["display_value"] == 71885000000.0
    assert indicators["TCMB_RESERVES_TOTAL"]["display_value"] == (82650 + 71885) * 1_000_000
    assert indicators["TCMB_RESERVES_TOTAL"]["source_dataset"] == "TCMB EVDS"


def test_evds_collector_parses_history_rows_from_transposed_payload(monkeypatch):
    collector = EVDSCollector()

    monkeypatch.setattr(
        collector,
        "_post_json",
        lambda path, payload, timeout=30: {
            "items": [
                {"Tarih": "24-05-2026", "TP_AB_C1": "81,440", "TP_AB_C2": "70,610"},
                {"Tarih": "31-05-2026", "TP_AB_C1": "82,650", "TP_AB_C2": "71,885"},
            ]
        },
    )

    history = collector.get_historical_data(
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2026, 6, 1),
        series_code="TP.AB.C1",
    )

    assert list(history.columns) == ["date", "value"]
    assert len(history) == 2
    assert history.iloc[-1]["value"] == 82650.0
