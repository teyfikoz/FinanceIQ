from __future__ import annotations

import html
import io
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

from app.core.config import settings
from app.services.cache import cache_get, cache_set
from app.services.snapshot_store import SnapshotStore
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KAPSiteScraper:
    DIRECTORY_URL = "https://www.kap.org.tr/tr/bist-sirketler"
    GENERAL_INFO_URL = "https://www.kap.org.tr/tr/sirket-bilgileri/genel/{perma_link}"
    DISCLOSURES_URL = "https://www.kap.org.tr/tr/api/company-detail/sgbf-data/{mkk_member_oid}/{notification_type}/{period}"
    DISCLOSURE_PDF_URL = "https://www.kap.org.tr/tr/api/BildirimPdf/{disclosure_index}"

    DIRECTORY_CACHE_KEY = "kap-site-directory-v1"
    DIRECTORY_SNAPSHOT_KEY = "kap-site-directory-v1"

    def __init__(
        self,
        ttl_seconds: int | None = None,
        snapshot_store: SnapshotStore | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds or settings.PUBLIC_RESEARCH_TTL_SECONDS
        self.snapshot_store = snapshot_store or SnapshotStore()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "text/html,application/json",
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                "User-Agent": "FundPilot/1.0 (+https://fundpilot.techsyncanalytica.com)",
            }
        )

    def _fetch_text(self, url: str) -> str:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def _fetch_json(self, url: str) -> Any:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def _fetch_bytes(self, url: str) -> bytes:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.content

    def _normalized_source(self, payload: str) -> str:
        return html.unescape(str(payload or "")).replace('\\"', '"')

    def _parse_stock_directory(self, payload: str) -> Dict[str, Dict[str, Any]]:
        source = self._normalized_source(payload)
        stock_pattern = re.compile(
            r'\{"mkkMemberOid":"[^"]+","kapMemberTitle":"[^"]+","relatedMemberTitle":"[^"]*","stockCode":"[^"]+","cityName":"[^"]*","relatedMemberOid":"[^"]*","kapMemberType":"[^"]+"\}'
        )
        permalink_pattern = re.compile(
            r'\{"mkkMemberOid":"[^"]+","kapMemberOid":"[^"]+","permaLink":"[^"]+","title":"[^"]+","fundCode":"[^"]+","fundOid":(?:null|"[^"]*")\}'
        )

        companies_by_mkk: Dict[str, Dict[str, Any]] = {}
        for match in stock_pattern.finditer(source):
            raw = json.loads(match.group(0))
            aliases = [alias.strip().upper() for alias in str(raw.get("stockCode") or "").split(",") if alias.strip()]
            if not aliases:
                continue
            companies_by_mkk[str(raw["mkkMemberOid"])] = {
                "mkk_member_oid": str(raw["mkkMemberOid"]),
                "company_title": str(raw.get("kapMemberTitle") or ""),
                "stock_codes": aliases,
                "city_name": str(raw.get("cityName") or ""),
                "company_type": str(raw.get("kapMemberType") or ""),
            }

        for match in permalink_pattern.finditer(source):
            raw = json.loads(match.group(0))
            entry = companies_by_mkk.setdefault(
                str(raw["mkkMemberOid"]),
                {
                    "mkk_member_oid": str(raw["mkkMemberOid"]),
                    "company_title": str(raw.get("title") or ""),
                    "stock_codes": [],
                },
            )
            if not entry.get("company_title"):
                entry["company_title"] = str(raw.get("title") or "")
            entry["kap_member_oid"] = str(raw.get("kapMemberOid") or "")
            entry["perma_link"] = str(raw.get("permaLink") or "")
            entry["fund_code"] = str(raw.get("fundCode") or "")

        by_symbol: Dict[str, Dict[str, Any]] = {}
        for entry in companies_by_mkk.values():
            for alias in entry.get("stock_codes", []):
                by_symbol[alias] = dict(entry)
        return by_symbol

    def _load_directory(self) -> Dict[str, Dict[str, Any]]:
        cached = cache_get(self.DIRECTORY_CACHE_KEY)
        if isinstance(cached, dict) and cached:
            return cached

        persisted = self.snapshot_store.read_json(self.DIRECTORY_SNAPSHOT_KEY)
        if isinstance(persisted, dict) and persisted:
            cache_set(self.DIRECTORY_CACHE_KEY, persisted, ttl=min(self.ttl_seconds, 3600))
            return persisted

        payload = self._fetch_text(self.DIRECTORY_URL)
        parsed = self._parse_stock_directory(payload)
        if parsed:
            cache_set(self.DIRECTORY_CACHE_KEY, parsed, ttl=min(self.ttl_seconds, 3600))
            self.snapshot_store.write_json(self.DIRECTORY_SNAPSHOT_KEY, parsed)
        return parsed

    def _extract_visible_lines(self, payload: str) -> List[str]:
        soup = BeautifulSoup(payload, "html.parser")
        for tag in soup(("script", "style", "noscript")):
            tag.decompose()
        return [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]

    def _parse_tr_number(self, value: str) -> float | None:
        text = str(value or "").strip()
        if not text:
            return None
        text = text.replace("\xa0", " ").replace("TL", "").replace("TRY", "").strip()
        text = re.sub(r"[^0-9,.\-]", "", text)
        if not text:
            return None
        if "." in text and "," in text:
            text = text.replace(".", "").replace(",", ".")
        elif text.count(".") > 1:
            text = text.replace(".", "")
        elif text.count(",") == 1 and text.count(".") == 0:
            left, right = text.split(",", 1)
            text = f"{left}.{right}" if len(right) <= 2 else f"{left}{right}"
        else:
            text = text.replace(",", "")
        try:
            return float(text)
        except Exception:
            return None

    def _value_after(self, lines: List[str], label: str, start_index: int = 0) -> str | None:
        for index in range(start_index, len(lines)):
            if lines[index] != label:
                continue
            for value in lines[index + 1 : index + 5]:
                if value and value != label:
                    return value
        return None

    def _parse_general_page(self, payload: str) -> Dict[str, Any]:
        lines = self._extract_visible_lines(payload)
        try:
            section_start = lines.index("SERMAYE VE ORTAKLIK YAPISI BİLGİLERİ")
        except ValueError:
            section_start = 0
        paid_in_capital_text = self._value_after(lines, "Ödenmiş/Çıkarılmış Sermaye", start_index=section_start)
        registered_capital_text = self._value_after(lines, "Kayıtlı Sermaye Tavanı", start_index=section_start)
        return {
            "paid_in_capital": self._parse_tr_number(paid_in_capital_text or ""),
            "registered_capital_ceiling": self._parse_tr_number(registered_capital_text or ""),
        }

    def _parse_publish_date(self, value: str | None) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        for fmt in ("%d.%m.%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d.%m.%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, fmt)
            except Exception:
                continue
        return None

    def _fetch_company_disclosures(self, mkk_member_oid: str, period: int = 365) -> List[Dict[str, Any]]:
        url = self.DISCLOSURES_URL.format(
            mkk_member_oid=mkk_member_oid,
            notification_type="ALL",
            period=int(period),
        )
        payload = self._fetch_json(url)
        return payload if isinstance(payload, list) else []

    def _contract_pdf_cache_key(self, disclosure_index: str) -> str:
        return f"kap-disclosure-signal:{disclosure_index}"

    def _contract_pdf_snapshot_key(self, disclosure_index: str) -> str:
        return f"kap-disclosure-signal-{disclosure_index}"

    def _extract_pdf_text(self, payload: bytes) -> str:
        try:
            from pypdf import PdfReader
        except Exception:
            logger.warning("pypdf is unavailable; KAP PDF extraction skipped")
            return ""

        try:
            reader = PdfReader(io.BytesIO(payload))
            parts = [(page.extract_text() or "").strip() for page in reader.pages]
            return "\n".join(part for part in parts if part)
        except Exception as exc:
            logger.warning("KAP PDF parsing failed", error=str(exc))
            return ""

    def _parse_amount_token(self, value: str | None) -> float | None:
        text = str(value or "").strip()
        if not text:
            return None
        text = re.sub(r"[^0-9,.\-]", "", text)
        if not text:
            return None
        if "." in text and "," in text:
            text = text.replace(".", "").replace(",", ".")
        elif text.count(".") > 1 and "," not in text:
            text = text.replace(".", "")
        elif text.count(",") > 1 and "." not in text:
            text = text.replace(",", "")
        elif text.count(",") == 1 and "." not in text:
            left, right = text.split(",", 1)
            text = f"{left}.{right}" if len(right) <= 2 else f"{left}{right}"
        else:
            text = text.replace(",", "")
        try:
            return float(text)
        except Exception:
            return None

    def _normalize_currency(self, token: str | None) -> str | None:
        text = str(token or "").strip().lower()
        if not text:
            return None
        if "abd dol" in text or "usd" in text or "us dol" in text or "amerikan dol" in text:
            return "USD"
        if "eur" in text or "euro" in text or "avro" in text:
            return "EUR"
        if "tl" in text or "try" in text or "türk liras" in text or "turk liras" in text:
            return "TRY"
        return None

    def _fx_rates_try(self) -> Dict[str, float]:
        cache_key = "kap-fx-rates-try-v1"
        cached = cache_get(cache_key)
        if isinstance(cached, dict) and cached:
            return {str(key): float(value) for key, value in cached.items() if value}

        rates = {"TRY": 1.0}
        try:
            import yfinance as yf

            for ticker, code in (("USDTRY=X", "USD"), ("EURTRY=X", "EUR")):
                history = yf.Ticker(ticker).history(period="5d", interval="1d")
                if history is None or history.empty:
                    continue
                close = history["Close"].dropna()
                if close.empty:
                    continue
                rates[code] = float(close.iloc[-1])
        except Exception as exc:
            logger.warning("FX conversion fetch failed for KAP disclosure parsing", error=str(exc))

        cache_set(cache_key, rates, ttl=min(self.ttl_seconds, 21600))
        return rates

    def _convert_to_try(self, amount: float | None, currency: str | None) -> float | None:
        numeric = self._parse_amount_token(amount)
        if numeric is None:
            return None
        if not currency or currency == "TRY":
            return numeric
        fx_rates = self._fx_rates_try()
        rate = self._parse_amount_token(fx_rates.get(currency))
        if rate is None or rate <= 0:
            return None
        return numeric * rate

    def _extract_contract_signal(self, text: str) -> Dict[str, Any]:
        payload = {
            "amount_value": None,
            "amount_currency": None,
            "amount_try": None,
            "sales_ratio": None,
        }
        normalized = str(text or "").replace("\xa0", " ")
        if not normalized.strip():
            return payload

        sales_share_patterns = [
            r"Net Satışlar/Satılan Mal Maliyeti\s*İçindeki Payı\s*%?\s*([0-9.,]+)",
            r"Net Satışlar[^%\n]{0,120}%\s*([0-9.,]+)",
        ]
        for pattern in sales_share_patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE | re.DOTALL)
            if not match:
                continue
            ratio = self._parse_amount_token(match.group(1))
            if ratio is not None:
                payload["sales_ratio"] = ratio / 100
                break

        amount_patterns = [
            r"toplam tutar[ıi]\s+([0-9.,]+)\s+(ABD Doları|Amerikan Doları|USD|US Doları|Euro|Avro|EUR|TL|TRY|Türk Lirası|Turk Lirası)",
            r"toplam bedel[ıi]\s+([0-9.,]+)\s+(ABD Doları|Amerikan Doları|USD|US Doları|Euro|Avro|EUR|TL|TRY|Türk Lirası|Turk Lirası)",
            r"tutar[ıi]\s+([0-9.,]+)\s+(ABD Doları|Amerikan Doları|USD|US Doları|Euro|Avro|EUR|TL|TRY|Türk Lirası|Turk Lirası)",
            r"bedel[ıi]\s+([0-9.,]+)\s+(ABD Doları|Amerikan Doları|USD|US Doları|Euro|Avro|EUR|TL|TRY|Türk Lirası|Turk Lirası)",
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if not match:
                continue
            amount_value = self._parse_amount_token(match.group(1))
            currency = self._normalize_currency(match.group(2))
            if amount_value is None:
                continue
            payload["amount_value"] = amount_value
            payload["amount_currency"] = currency
            payload["amount_try"] = self._convert_to_try(amount_value, currency)
            break
        return payload

    def _contract_candidate(self, basic: Dict[str, Any]) -> bool:
        text = " ".join(
            [
                str(basic.get("title") or ""),
                str(basic.get("summary") or ""),
            ]
        ).lower()
        keywords = (
            "yeni iş ilişkisi",
            "sözleşme",
            "sipariş",
            "ihale",
            "order",
            "contract",
            "tender",
        )
        return any(keyword in text for keyword in keywords)

    def _canonical_disclosure_key(self, basic: Dict[str, Any]) -> str:
        for candidate in (
            basic.get("relatedDisclosureOid"),
            basic.get("disclosureId"),
            basic.get("disclosureIndex"),
        ):
            if candidate:
                return str(candidate)
        return str(basic.get("publishDate") or "")

    def _get_disclosure_signal(self, disclosure_index: Any) -> Dict[str, Any]:
        disclosure_id = str(disclosure_index or "").strip()
        if not disclosure_id:
            return {}

        cache_key = self._contract_pdf_cache_key(disclosure_id)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        persisted = self.snapshot_store.read_json(self._contract_pdf_snapshot_key(disclosure_id))
        if isinstance(persisted, dict):
            cache_set(cache_key, persisted, ttl=min(self.ttl_seconds, 86400))
            return persisted

        try:
            payload = self._fetch_bytes(self.DISCLOSURE_PDF_URL.format(disclosure_index=disclosure_id))
            text = self._extract_pdf_text(payload)
            signal = self._extract_contract_signal(text)
            signal["extracted"] = bool(signal.get("sales_ratio") is not None or signal.get("amount_try") is not None)
            cache_set(cache_key, signal, ttl=min(self.ttl_seconds, 86400))
            self.snapshot_store.write_json(self._contract_pdf_snapshot_key(disclosure_id), signal)
            return signal
        except Exception as exc:
            logger.warning("KAP disclosure PDF parse failed", disclosure_index=disclosure_id, error=str(exc))
            return {}

    def _disclosure_momentum_score(
        self,
        disclosures_30d: int,
        material_90d: int,
        contract_mentions_365d: int,
        extracted_signals: int,
    ) -> float:
        score = 18.0
        score += min(disclosures_30d * 2.5, 18.0)
        score += min(material_90d * 4.0, 24.0)
        score += min(contract_mentions_365d * 3.0, 24.0)
        score += min(extracted_signals * 4.0, 16.0)
        return max(0.0, min(100.0, score))

    def get_company_payload(self, symbol: str) -> Dict[str, Any]:
        symbol_root = str(symbol or "").split(".")[0].upper()
        if not symbol_root:
            return {}

        directory = self._load_directory()
        company = directory.get(symbol_root)
        if not isinstance(company, dict):
            return {}

        payload: Dict[str, Any] = {
            "symbol_root": symbol_root,
            "company_title": company.get("company_title"),
            "mkk_member_oid": company.get("mkk_member_oid"),
            "perma_link": company.get("perma_link"),
            "stock_codes": list(company.get("stock_codes", [])),
            "capital_method": "Public KAP company general page",
            "coverage_note": "KAP public general page and public disclosure feed were parsed successfully.",
        }

        perma_link = str(company.get("perma_link") or "")
        if perma_link:
            try:
                general_payload = self._fetch_text(self.GENERAL_INFO_URL.format(perma_link=perma_link))
                payload.update(self._parse_general_page(general_payload))
            except Exception as exc:
                logger.warning("KAP general page parse failed", symbol=symbol_root, error=str(exc))

        mkk_member_oid = str(company.get("mkk_member_oid") or "")
        if mkk_member_oid:
            try:
                disclosures = self._fetch_company_disclosures(mkk_member_oid, period=365)
                own_disclosures: List[Dict[str, Any]] = []
                for item in disclosures:
                    basic = item.get("disclosureBasic") if isinstance(item, dict) else None
                    if not isinstance(basic, dict):
                        continue
                    if str(basic.get("mkkMemberOid") or "") != mkk_member_oid:
                        continue
                    own_disclosures.append(item)

                breakdown: Dict[str, int] = {}
                recent_cutoff = datetime.utcnow() - timedelta(days=30)
                quarter_cutoff = datetime.utcnow() - timedelta(days=90)
                recent_count = 0
                recent_count_90d = 0
                material_disclosures_90d = 0
                last_disclosure: datetime | None = None
                contract_candidates: Dict[str, Dict[str, Any]] = {}
                for item in own_disclosures:
                    basic = item.get("disclosureBasic") or {}
                    disclosure_class = str(basic.get("disclosureClass") or basic.get("disclosureType") or "UNKNOWN")
                    breakdown[disclosure_class] = breakdown.get(disclosure_class, 0) + 1
                    published_at = self._parse_publish_date(basic.get("publishDate"))
                    canonical_key = self._canonical_disclosure_key(basic)
                    if published_at is not None:
                        if last_disclosure is None or published_at > last_disclosure:
                            last_disclosure = published_at
                        if published_at >= recent_cutoff:
                            recent_count += 1
                        if published_at >= quarter_cutoff:
                            recent_count_90d += 1
                            if disclosure_class == "ODA":
                                material_disclosures_90d += 1
                    if self._contract_candidate(basic):
                        existing = contract_candidates.get(canonical_key)
                        existing_basic = existing.get("disclosureBasic") if isinstance(existing, dict) else {}
                        existing_published = self._parse_publish_date(existing_basic.get("publishDate")) if isinstance(existing_basic, dict) else None
                        if existing is None or (published_at and (existing_published is None or published_at > existing_published)):
                            contract_candidates[canonical_key] = item

                contract_value_ttm = 0.0
                contract_value_found = False
                contract_to_sales_ratio_ttm = 0.0
                contract_ratio_found = False
                extracted_contract_signals = 0
                contract_examples: List[str] = []
                sorted_candidates = sorted(
                    contract_candidates.values(),
                    key=lambda disclosure: self._parse_publish_date((disclosure.get("disclosureBasic") or {}).get("publishDate")) or datetime.min,
                    reverse=True,
                )
                for item in sorted_candidates:
                    basic = item.get("disclosureBasic") or {}
                    disclosure_index = basic.get("disclosureIndex")
                    if disclosure_index is None:
                        continue
                    signal = self._get_disclosure_signal(disclosure_index)
                    if signal.get("extracted"):
                        extracted_contract_signals += 1
                    amount_try = self._parse_amount_token(signal.get("amount_try"))
                    if amount_try is not None:
                        contract_value_ttm += amount_try
                        contract_value_found = True
                    sales_ratio = self._parse_amount_token(signal.get("sales_ratio"))
                    if sales_ratio is not None:
                        contract_to_sales_ratio_ttm += sales_ratio
                        contract_ratio_found = True
                    summary_text = str(basic.get("summary") or basic.get("title") or "").strip()
                    if summary_text and summary_text not in contract_examples:
                        contract_examples.append(summary_text)

                contract_signal_confidence = "none"
                if contract_candidates and extracted_contract_signals:
                    contract_signal_confidence = "exact"
                elif contract_candidates:
                    contract_signal_confidence = "mention-only"

                payload.update(
                    {
                        "disclosures_count": float(len(own_disclosures)) if own_disclosures else None,
                        "disclosures_count_30d": float(recent_count) if own_disclosures else None,
                        "disclosures_count_90d": float(recent_count_90d) if own_disclosures else None,
                        "disclosures_count_365d": len(own_disclosures),
                        "last_disclosure_date": last_disclosure.date().isoformat() if last_disclosure else None,
                        "material_disclosures_90d": material_disclosures_90d if own_disclosures else None,
                        "contract_mentions_365d": len(contract_candidates),
                        "contract_to_sales_ratio_ttm": contract_to_sales_ratio_ttm if contract_ratio_found else None,
                        "contract_value_ttm": contract_value_ttm if contract_value_found else None,
                        "contract_signal_confidence": contract_signal_confidence,
                        "contract_examples": contract_examples[:5],
                        "disclosure_momentum_score": self._disclosure_momentum_score(
                            recent_count,
                            material_disclosures_90d,
                            len(contract_candidates),
                            extracted_contract_signals,
                        ),
                        "notification_breakdown": breakdown,
                        "raw_payload_present": bool(own_disclosures),
                    }
                )
            except Exception as exc:
                logger.warning("KAP disclosures fetch failed", symbol=symbol_root, error=str(exc))

        return payload
