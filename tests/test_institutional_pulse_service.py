from tempfile import TemporaryDirectory

from app.services.institutional_pulse import InstitutionalPulseService
from app.services.snapshot_store import SnapshotStore


SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<informationTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable">
  <infoTable>
    <nameOfIssuer>APPLE INC</nameOfIssuer>
    <titleOfClass>COM</titleOfClass>
    <cusip>037833100</cusip>
    <value>1000</value>
    <shrsOrPrnAmt>
      <sshPrnamt>5000</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
    <investmentDiscretion>SOLE</investmentDiscretion>
  </infoTable>
  <infoTable>
    <nameOfIssuer>MICROSOFT CORP</nameOfIssuer>
    <titleOfClass>COM</titleOfClass>
    <cusip>594918104</cusip>
    <value>500</value>
    <shrsOrPrnAmt>
      <sshPrnamt>2500</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
    <investmentDiscretion>SOLE</investmentDiscretion>
  </infoTable>
</informationTable>
"""

SAMPLE_XML_DOLLARS = """<?xml version="1.0" encoding="UTF-8"?>
<informationTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable">
  <infoTable>
    <nameOfIssuer>APPLE INC</nameOfIssuer>
    <titleOfClass>COM</titleOfClass>
    <cusip>037833100</cusip>
    <value>400000000</value>
    <shrsOrPrnAmt>
      <sshPrnamt>10000000</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
  </infoTable>
  <infoTable>
    <nameOfIssuer>APPLE INC</nameOfIssuer>
    <titleOfClass>COM</titleOfClass>
    <cusip>037833100</cusip>
    <value>100000000</value>
    <shrsOrPrnAmt>
      <sshPrnamt>2500000</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
  </infoTable>
</informationTable>
"""


def test_parse_information_table_xml_extracts_holdings():
    service = InstitutionalPulseService()

    frame = service._parse_information_table_xml(SAMPLE_XML)

    assert len(frame) == 2
    assert frame.iloc[0]["issuer"] == "APPLE INC"
    assert frame.iloc[0]["value_usd"] == 1_000_000
    assert round(float(frame["portfolio_weight"].sum()), 3) == 100.0


def test_compare_holdings_frames_detects_new_and_decreased():
    service = InstitutionalPulseService()
    current = service._parse_information_table_xml(SAMPLE_XML)
    previous = current.copy()
    previous.loc[previous["issuer"] == "APPLE INC", "value_usd"] = 1_500_000
    previous.loc[previous["issuer"] == "APPLE INC", "portfolio_weight"] = 75.0
    previous = previous[previous["issuer"] != "MICROSOFT CORP"].reset_index(drop=True)

    changes = service._compare_holdings_frames(current, previous)

    apple = changes[changes["issuer"] == "APPLE INC"].iloc[0]
    microsoft = changes[changes["issuer"] == "MICROSOFT CORP"].iloc[0]

    assert apple["action"] == "DECREASED"
    assert microsoft["action"] == "NEW"


def test_parse_information_table_xml_aggregates_duplicate_rows_when_values_are_in_dollars():
    service = InstitutionalPulseService()

    frame = service._parse_information_table_xml(SAMPLE_XML_DOLLARS)

    assert len(frame) == 1
    assert frame.iloc[0]["issuer"] == "APPLE INC"
    assert frame.iloc[0]["value_usd"] == 500_000_000
    assert frame.iloc[0]["shares"] == 12_500_000


def test_workspace_uses_snapshot_when_live_refresh_fails(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=tmpdir)
        service = InstitutionalPulseService(snapshot_store=snapshot_store)
        snapshot_store.write_json(
            service._dataset_snapshot_key("berkshire"),
            {
                "selected_manager": "berkshire",
                "manager": service.MANAGERS["berkshire"],
                "source_state": "live",
                "generated_at": "2026-05-28T00:00:00Z",
                "latest_filing": {"filing_date": "2026-05-15", "form": "13F-HR"},
                "previous_filing": None,
                "current_rows": [],
                "changes_rows": [],
                "summary": {
                    "portfolio_value": "$10.0B",
                    "holding_count": 10,
                    "top_10_weight": "+80.0%",
                    "option_exposure": "+0.0%",
                    "largest_position": "APPLE INC",
                    "largest_position_weight": "+20.0%",
                    "filing_lag_days": 10,
                    "new_positions": 1,
                    "exited_positions": 0,
                },
            },
        )
        monkeypatch.setattr(service, "_build_dataset", lambda manager_key: (_ for _ in ()).throw(RuntimeError("upstream failed")))

        dataset = service.get_manager_dataset("berkshire")

        assert dataset["source_state"] == "snapshot"
        assert dataset["warning"].startswith("Live SEC refresh failed")


def test_get_symbol_signal_summarizes_curated_manager_positioning(monkeypatch):
    service = InstitutionalPulseService()

    datasets = {
        "berkshire": {
            "selected_manager": "berkshire",
            "manager": service.MANAGERS["berkshire"],
            "source_state": "live",
            "latest_filing": {"filing_date": "2026-05-15"},
            "current_rows": [
                {"issuer": "APPLE INC", "issuer_key": "APPLE", "value_usd": 57_800_000_000, "portfolio_weight": 22.0},
            ],
            "changes_rows": [
                {"issuer": "APPLE INC", "issuer_key": "APPLE", "action": "DECREASED", "weight_change": -0.6},
            ],
        },
        "bridgewater": {
            "selected_manager": "bridgewater",
            "manager": service.MANAGERS["bridgewater"],
            "source_state": "live",
            "latest_filing": {"filing_date": "2026-05-15"},
            "current_rows": [
                {"issuer": "APPLE INC", "issuer_key": "APPLE", "value_usd": 1_500_000_000, "portfolio_weight": 0.6},
            ],
            "changes_rows": [
                {"issuer": "APPLE INC", "issuer_key": "APPLE", "action": "NEW", "weight_change": 0.6},
            ],
        },
        "gates": {
            "selected_manager": "gates",
            "manager": service.MANAGERS["gates"],
            "source_state": "live",
            "latest_filing": {"filing_date": "2026-05-15"},
            "current_rows": [],
            "changes_rows": [
                {"issuer": "APPLE INC", "issuer_key": "APPLE", "action": "SOLD", "weight_change": -0.8},
            ],
        },
        "pershing": {
            "selected_manager": "pershing",
            "manager": service.MANAGERS["pershing"],
            "source_state": "live",
            "latest_filing": {"filing_date": "2026-05-15"},
            "current_rows": [],
            "changes_rows": [],
        },
        "duquesne": {
            "selected_manager": "duquesne",
            "manager": service.MANAGERS["duquesne"],
            "source_state": "live",
            "latest_filing": {"filing_date": "2026-05-15"},
            "current_rows": [],
            "changes_rows": [],
        },
    }

    monkeypatch.setattr(service, "get_manager_dataset", lambda manager_key: datasets[manager_key])

    signal = service.get_symbol_signal("AAPL", "Apple Inc.")

    assert signal["available"] is True
    assert signal["signal"] == "Distribution"
    assert signal["summary"]["holder_count"] == 2
    assert signal["summary"]["top_holder"] == "Warren Buffett"
    assert signal["exited_rows"][0]["manager"] == "Bill Gates"


def test_get_health_snapshot_counts_live_snapshot_and_warming(monkeypatch):
    service = InstitutionalPulseService()
    datasets = {
        "berkshire": {
            "selected_manager": "berkshire",
            "manager": service.MANAGERS["berkshire"],
            "source_state": "live",
            "latest_filing": {"filing_date": "2026-05-15"},
            "summary": {"holding_count": 40, "portfolio_value": "$300.0B", "largest_position": "APPLE INC", "top_10_weight": "+84.0%", "new_positions": 2, "exited_positions": 1, "filing_lag_days": 12},
        },
        "gates": {
            "selected_manager": "gates",
            "manager": service.MANAGERS["gates"],
            "source_state": "snapshot",
            "latest_filing": {"filing_date": "2026-05-15"},
            "summary": {"holding_count": 22, "portfolio_value": "$40.0B", "largest_position": "MSFT", "top_10_weight": "+70.0%", "new_positions": 1, "exited_positions": 0, "filing_lag_days": 12},
        },
        "bridgewater": {
            "selected_manager": "bridgewater",
            "manager": service.MANAGERS["bridgewater"],
            "source_state": "warming",
            "latest_filing": None,
            "summary": {"holding_count": 0, "portfolio_value": "N/A", "largest_position": "N/A", "top_10_weight": "N/A", "new_positions": 0, "exited_positions": 0, "filing_lag_days": 0},
        },
        "pershing": {
            "selected_manager": "pershing",
            "manager": service.MANAGERS["pershing"],
            "source_state": "live",
            "latest_filing": {"filing_date": "2026-05-14"},
            "summary": {"holding_count": 10, "portfolio_value": "$12.0B", "largest_position": "HHH", "top_10_weight": "+92.0%", "new_positions": 0, "exited_positions": 0, "filing_lag_days": 13},
        },
        "duquesne": {
            "selected_manager": "duquesne",
            "manager": service.MANAGERS["duquesne"],
            "source_state": "live",
            "latest_filing": {"filing_date": "2026-05-15"},
            "summary": {"holding_count": 35, "portfolio_value": "$3.0B", "largest_position": "NVDA", "top_10_weight": "+58.0%", "new_positions": 4, "exited_positions": 1, "filing_lag_days": 12},
        },
    }

    monkeypatch.setattr(service, "get_manager_dataset", lambda manager_key: datasets[manager_key])

    health = service.get_health_snapshot()

    assert health["state"] == "degraded"
    assert health["summary"]["manager_count"] == 5
    assert health["summary"]["live_count"] == 3
    assert health["summary"]["snapshot_count"] == 1
    assert health["summary"]["warming_count"] == 1
