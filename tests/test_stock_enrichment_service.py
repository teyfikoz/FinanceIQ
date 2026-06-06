from pathlib import Path
from tempfile import TemporaryDirectory

from app.services.cache import cache_clear
from app.services.snapshot_store import SnapshotStore
from app.services.stock_enrichment import StockEnrichmentService


def test_stock_enrichment_service_normalizes_nested_kap_payload(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = StockEnrichmentService(snapshot_store=snapshot_store)
        payload = {
            "company": {
                "odenmis_sermaye": 900_000_000,
            },
            "financials": {
                "new_business_value": 2_500_000_000,
            },
            "contract_to_sales_ratio_ttm": 0.18,
            "material_disclosures_90d": 4,
            "contract_mentions_365d": 3,
            "disclosure_momentum_score": 72.0,
            "announcements": [
                {"announcement_date": "2026-05-20", "title": "Contract A"},
                {"announcement_date": "2026-05-28", "title": "Contract B"},
            ],
        }
        monkeypatch.setattr(service, "_fetch_company_payload", lambda symbol_root: payload)

        enrichment = service.get_kap_enrichment("ASELS", force_refresh=True)

        assert enrichment["source_state"] == "live"
        assert enrichment["paid_in_capital"] == 900_000_000
        assert enrichment["contract_value_ttm"] == 2_500_000_000
        assert enrichment["contract_to_sales_ratio_ttm"] == 0.18
        assert enrichment["disclosures_count"] == 2.0
        assert enrichment["material_disclosures_90d"] == 4
        assert enrichment["contract_mentions_365d"] == 3
        assert enrichment["disclosure_momentum_score"] == 72.0
        assert enrichment["last_disclosure_date"] == "2026-05-28"
        assert enrichment["field_coverage"] >= 4


def test_stock_enrichment_service_falls_back_to_persisted_snapshot(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = StockEnrichmentService(snapshot_store=snapshot_store)
        persisted = {
            "symbol_root": "THYAO",
            "source_state": "live",
            "saved_at": "2026-05-29T00:00:00Z",
            "raw_payload_present": True,
            "field_coverage": 3,
            "paid_in_capital": 1_380_000_000,
            "capital_method": "Exact KAP field via enrichment snapshot",
            "contract_value_ttm": 4_800_000_000,
            "backlog_value": None,
            "disclosures_count": 12,
            "last_disclosure_date": "2026-05-27",
            "coverage_note": "Structured KAP enrichment is live.",
        }
        snapshot_store.write_json(service._snapshot_key("THYAO"), persisted)
        monkeypatch.setattr(service, "_fetch_company_payload", lambda symbol_root: {})

        enrichment = service.get_kap_enrichment("THYAO", force_refresh=True)

        assert enrichment["source_state"] == "persisted-fallback"
        assert enrichment["paid_in_capital"] == 1_380_000_000
        assert enrichment["last_disclosure_date"] == "2026-05-27"
        assert "using the last persisted enrichment snapshot" in enrichment["stale_notice"]


def test_stock_enrichment_service_prefers_public_kap_site_payload(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = StockEnrichmentService(snapshot_store=snapshot_store)
        payload = {
            "paid_in_capital": 1_926_795_598,
            "contract_value_ttm": 17_000_000_000,
            "contract_to_sales_ratio_ttm": 0.4115,
            "disclosures_count": 6,
            "material_disclosures_90d": 3,
            "contract_mentions_365d": 2,
            "disclosure_momentum_score": 78.0,
            "last_disclosure_date": "2026-05-11",
            "capital_method": "Public KAP company general page",
            "coverage_note": "KAP public general page and public disclosure feed were parsed successfully.",
            "raw_payload_present": True,
        }
        monkeypatch.setattr(service, "_fetch_company_payload", lambda symbol_root: payload)

        enrichment = service.get_kap_enrichment("TUPRS", force_refresh=True)

        assert enrichment["source_state"] == "live"
        assert enrichment["paid_in_capital"] == 1_926_795_598
        assert enrichment["disclosures_count"] == 6
        assert enrichment["contract_to_sales_ratio_ttm"] == 0.4115
        assert enrichment["material_disclosures_90d"] == 3
        assert enrichment["contract_mentions_365d"] == 2
        assert enrichment["disclosure_momentum_score"] == 78.0
        assert enrichment["last_disclosure_date"] == "2026-05-11"
        assert enrichment["capital_method"] == "Public KAP company general page"
        assert enrichment["coverage_note"].startswith("KAP public general page")


def test_stock_enrichment_health_snapshot_counts_live_and_fallback(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = StockEnrichmentService(snapshot_store=snapshot_store)
        payloads = {
            "ASELS": {
                "source_state": "live",
                "saved_at": "2026-06-01T10:00:00Z",
                "field_coverage": 5,
                "last_disclosure_date": "2026-05-30",
                "contract_to_sales_ratio_ttm": 0.42,
                "disclosure_momentum_score": 91.0,
                "coverage_note": "live",
            },
            "THYAO": {
                "source_state": "persisted-fallback",
                "saved_at": "2026-05-31T10:00:00Z",
                "field_coverage": 3,
                "last_disclosure_date": "2026-05-29",
                "contract_to_sales_ratio_ttm": None,
                "disclosure_momentum_score": 68.0,
                "coverage_note": "fallback",
            },
            "TUPRS": {
                "source_state": "unavailable",
                "saved_at": None,
                "field_coverage": 0,
                "last_disclosure_date": None,
                "contract_to_sales_ratio_ttm": None,
                "disclosure_momentum_score": None,
                "coverage_note": "unavailable",
            },
        }
        monkeypatch.setattr(
            service,
            "get_kap_enrichment",
            lambda symbol, force_refresh=False: payloads[str(symbol).upper()],
        )

        snapshot = service.get_health_snapshot(symbols=("ASELS", "THYAO", "TUPRS"))

        assert snapshot["state"] == "degraded"
        assert snapshot["summary"]["symbols_tracked"] == 3
        assert snapshot["summary"]["live_count"] == 1
        assert snapshot["summary"]["fallback_count"] == 1
        assert snapshot["summary"]["unavailable_count"] == 1
        assert snapshot["summary"]["latest_disclosure_date"] == "2026-05-30"
        assert snapshot["rows"][0]["symbol"] == "ASELS"
