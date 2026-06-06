from pathlib import Path
from tempfile import TemporaryDirectory

from app.services.cache import cache_clear
from app.services.kap_site_scraper import KAPSiteScraper
from app.services.snapshot_store import SnapshotStore


def test_kap_site_scraper_joins_directory_general_and_disclosures(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        scraper = KAPSiteScraper(snapshot_store=snapshot_store)

        directory_html = """
        <script>
        companyPermaLinks":[
            {"mkkMemberOid":"mkk-tuprs","kapMemberOid":"kap-tuprs","permaLink":"1105-tupras-turkiye-petrol-rafinerileri-a-s","title":"TÜPRAŞ-TÜRKİYE PETROL RAFİNERİLERİ A.Ş.","fundCode":"1105","fundOid":null},
            {"mkkMemberOid":"mkk-garan","kapMemberOid":"kap-garan","permaLink":"2422-turkiye-garanti-bankasi-a-s","title":"TÜRKİYE GARANTİ BANKASI A.Ş.","fundCode":"2422","fundOid":null}
        ]
        [
            {"mkkMemberOid":"mkk-tuprs","kapMemberTitle":"TÜPRAŞ-TÜRKİYE PETROL RAFİNERİLERİ A.Ş.","relatedMemberTitle":"AUDIT A.Ş.","stockCode":"TUPRS","cityName":"İSTANBUL","relatedMemberOid":"r1","kapMemberType":"IGS"},
            {"mkkMemberOid":"mkk-garan","kapMemberTitle":"TÜRKİYE GARANTİ BANKASI A.Ş.","relatedMemberTitle":"AUDIT A.Ş.","stockCode":"GARAN, TGB","cityName":"İSTANBUL","relatedMemberOid":"r2","kapMemberType":"IGS"}
        ]
        </script>
        """
        general_html = """
        <html><body>
        <div>SERMAYE VE ORTAKLIK YAPISI BİLGİLERİ</div>
        <div>Ödenmiş/Çıkarılmış Sermaye</div>
        <div>1.926.795.598</div>
        <div>Kayıtlı Sermaye Tavanı</div>
        <div>10.000.000.000</div>
        </body></html>
        """
        disclosures_payload = [
            {
                "disclosureBasic": {
                    "mkkMemberOid": "mkk-tuprs",
                    "disclosureClass": "ODA",
                    "title": "Yeni İş İlişkisi",
                    "summary": "Sözleşme İmzalanması",
                    "publishDate": "11.05.2026 18:22:51",
                    "stockCode": "TUPRS",
                    "disclosureIndex": 1609287,
                    "disclosureId": "disclosure-1",
                }
            },
            {
                "disclosureBasic": {
                    "mkkMemberOid": "mkk-tuprs",
                    "disclosureClass": "FR",
                    "publishDate": "06.05.2026 18:18:37",
                    "stockCode": "TUPRS",
                    "disclosureIndex": 1609286,
                    "disclosureId": "disclosure-2",
                }
            },
            {
                "disclosureBasic": {
                    "mkkMemberOid": "other-company",
                    "disclosureClass": "ODA",
                    "publishDate": "08.05.2026 18:15:22",
                    "stockCode": "BJKAS",
                }
            },
        ]

        def fake_fetch_text(url: str) -> str:
            if url.endswith("/tr/bist-sirketler"):
                return directory_html
            if "sirket-bilgileri/genel/" in url:
                return general_html
            raise AssertionError(f"unexpected text url: {url}")

        def fake_fetch_json(url: str):
            assert "api/company-detail/sgbf-data/mkk-tuprs/ALL/365" in url
            return disclosures_payload

        monkeypatch.setattr(scraper, "_fetch_text", fake_fetch_text)
        monkeypatch.setattr(scraper, "_fetch_json", fake_fetch_json)
        monkeypatch.setattr(
            scraper,
            "_get_disclosure_signal",
            lambda disclosure_index: {
                "sales_ratio": 0.4115,
                "amount_try": 17_000_000_000.0,
                "extracted": True,
            }
            if str(disclosure_index) == "1609287"
            else {},
        )

        payload = scraper.get_company_payload("TUPRS")

        assert payload["mkk_member_oid"] == "mkk-tuprs"
        assert payload["perma_link"] == "1105-tupras-turkiye-petrol-rafinerileri-a-s"
        assert payload["paid_in_capital"] == 1_926_795_598.0
        assert payload["registered_capital_ceiling"] == 10_000_000_000.0
        assert payload["disclosures_count"] == 2.0
        assert payload["disclosures_count_365d"] == 2
        assert payload["last_disclosure_date"] == "2026-05-11"
        assert payload["notification_breakdown"] == {"ODA": 1, "FR": 1}
        assert payload["material_disclosures_90d"] == 1
        assert payload["contract_mentions_365d"] == 1
        assert payload["contract_to_sales_ratio_ttm"] == 0.4115
        assert payload["contract_value_ttm"] == 17_000_000_000.0
        assert payload["contract_signal_confidence"] == "exact"


def test_kap_site_scraper_supports_stock_code_aliases(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        scraper = KAPSiteScraper(snapshot_store=snapshot_store)

        directory_html = """
        <script>
        companyPermaLinks":[
            {"mkkMemberOid":"mkk-garan","kapMemberOid":"kap-garan","permaLink":"2422-turkiye-garanti-bankasi-a-s","title":"TÜRKİYE GARANTİ BANKASI A.Ş.","fundCode":"2422","fundOid":null}
        ]
        [
            {"mkkMemberOid":"mkk-garan","kapMemberTitle":"TÜRKİYE GARANTİ BANKASI A.Ş.","relatedMemberTitle":"AUDIT A.Ş.","stockCode":"GARAN, TGB","cityName":"İSTANBUL","relatedMemberOid":"r2","kapMemberType":"IGS"}
        ]
        </script>
        """

        monkeypatch.setattr(scraper, "_fetch_text", lambda url: directory_html)
        directory = scraper._load_directory()

        assert directory["GARAN"]["mkk_member_oid"] == "mkk-garan"
        assert directory["TGB"]["perma_link"] == "2422-turkiye-garanti-bankasi-a-s"


def test_kap_site_scraper_extracts_contract_signal_from_pdf_text():
    scraper = KAPSiteScraper()
    text = """
    Yeni İş İlişkisi
    Varsa Müşterinin/Tedarikçinin Ortaklığın Kamuya Açıklanan Son Gelir Tablosundaki Net Satışlar/Satılan Mal Maliyeti İçindeki Payı
    %41,15
    Açıklamalar
    toplam tutarı 469.974.000 ABD Doları olan sözleşmeler imzalanmıştır.
    """

    signal = scraper._extract_contract_signal(text)

    assert round(signal["sales_ratio"], 4) == 0.4115
    assert signal["amount_value"] == 469_974_000.0
    assert signal["amount_currency"] == "USD"
