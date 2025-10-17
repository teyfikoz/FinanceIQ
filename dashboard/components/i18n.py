"""
Internationalization (i18n) Module
Simple translation system for Turkish/English support.
"""

from typing import Dict, Optional

# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'en': {
        # Common
        'title': 'Global Liquidity Dashboard',
        'settings': 'Settings',
        'refresh': 'Refresh Data',
        'export': 'Export',
        'loading': 'Loading...',
        'error': 'Error',
        'success': 'Success',
        'warning': 'Warning',
        'info': 'Info',

        # Income Statement
        'income_sankey_title': 'Income Statement Sankey',
        'income_sankey_subtitle': 'Visualize financial flows from revenue to net income',
        'ticker_symbol': 'Ticker Symbol',
        'period': 'Period',
        'annual': 'Annual',
        'quarterly': 'Quarterly',
        'select_period': 'Select Period',
        'show_yoy': 'Show YoY Changes',
        'revenue': 'Revenue',
        'gross_margin': 'Gross Margin',
        'operating_margin': 'Operating Margin',
        'net_margin': 'Net Margin',
        'income_flow': 'Income Statement Flow',
        'detailed_metrics': 'Detailed Metrics',
        'operating_expenses': 'Operating Expenses',
        'historical_summary': 'Historical Summary',

        # Fund Holdings
        'fund_sankey_title': 'Fund Holdings & Ownership Sankey',
        'fund_sankey_subtitle': 'Visualize ETF/Fund holdings and stock ownership patterns',
        'fund_to_stocks': 'Fund → Stocks',
        'stock_to_funds': 'Stock → Funds',
        'fund_symbol': 'Fund/ETF Symbol',
        'top_n_holdings': 'Top N Holdings',
        'stock_symbol': 'Stock Symbol',
        'select_funds': 'Select Funds to Check',
        'holdings_count': 'Total Holdings Shown',
        'total_weight': 'Total Weight',
        'top3_concentration': 'Top 3 Concentration',
        'funds_holding': 'Funds Holding',
        'max_weight': 'Max Weight',
        'avg_weight': 'Avg Weight',
        'holdings_details': 'Holdings Details',
        'ownership_details': 'Ownership Details',

        # Macro Liquidity
        'macro_sankey_title': 'Macro Liquidity Flow Sankey',
        'macro_sankey_subtitle': 'Visualize global liquidity flows from sources to risk assets',
        'liquidity_sources': 'Liquidity Sources',
        'include_m2': 'Include M2',
        'm2_weight': 'M2 Weight',
        'include_cb': 'Include Central Bank Balance Sheets',
        'cb_weight': 'CB Balance Weight',
        'include_gli': 'Include Global Liquidity Index',
        'gli_weight': 'GLI Weight',
        'asset_allocations': 'Asset Allocations',
        'equities_allocation': 'Equities Allocation',
        'btc_allocation': 'Bitcoin Allocation',
        'gold_allocation': 'Gold Allocation',
        'liquidity_overview': 'Liquidity Overview',
        'total_liquidity_score': 'Total Liquidity Score',
        'total_asset_allocation': 'Total Asset Allocation',
        'sources_active': 'Sources Active',
        'asset_classes': 'Asset Classes',
        'liquidity_flow_viz': 'Liquidity Flow Visualization',
        'insights': 'Insights',
        'about_macro': 'About Macro Liquidity',

        # Export
        'export_options': 'Export Options',
        'download_png': 'Download PNG',
        'download_html': 'Download HTML',
        'download_csv': 'Download CSV',

        # Messages
        'no_data_found': 'No financial data found for {ticker}. Please check the ticker symbol and try again.',
        'try_tickers': 'Try common tickers like: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA',
        'no_holdings_found': 'No holdings data found for {symbol}',
        'try_funds': 'Try popular ETFs: SPY, QQQ, VOO, ARKK, VT, IWM, VTI',
        'select_at_least_one_fund': 'Please select at least one fund to check',
        'select_liquidity_source': 'Please select at least one liquidity source',
        'set_asset_allocation': 'Please set at least one asset allocation > 0',
        'data_cached': 'Data sources: FMP, Alpha Vantage, Yahoo Finance | Cached for performance',
    },

    'tr': {
        # Common
        'title': 'Küresel Likidite Gösterge Paneli',
        'settings': 'Ayarlar',
        'refresh': 'Veriyi Yenile',
        'export': 'Dışa Aktar',
        'loading': 'Yükleniyor...',
        'error': 'Hata',
        'success': 'Başarılı',
        'warning': 'Uyarı',
        'info': 'Bilgi',

        # Income Statement
        'income_sankey_title': 'Gelir Tablosu Sankey',
        'income_sankey_subtitle': 'Gelirden net gelire mali akışları görselleştirin',
        'ticker_symbol': 'Hisse Senedi Sembolü',
        'period': 'Dönem',
        'annual': 'Yıllık',
        'quarterly': 'Çeyreklik',
        'select_period': 'Dönem Seç',
        'show_yoy': 'Yıllık Değişimleri Göster',
        'revenue': 'Gelir',
        'gross_margin': 'Brüt Kar Marjı',
        'operating_margin': 'Faaliyet Kar Marjı',
        'net_margin': 'Net Kar Marjı',
        'income_flow': 'Gelir Tablosu Akışı',
        'detailed_metrics': 'Detaylı Metrikler',
        'operating_expenses': 'Faaliyet Giderleri',
        'historical_summary': 'Geçmiş Özet',

        # Fund Holdings
        'fund_sankey_title': 'Fon Varlıkları & Sahiplik Sankey',
        'fund_sankey_subtitle': 'ETF/Fon varlıklarını ve hisse senedi sahiplik kalıplarını görselleştirin',
        'fund_to_stocks': 'Fon → Hisseler',
        'stock_to_funds': 'Hisse → Fonlar',
        'fund_symbol': 'Fon/ETF Sembolü',
        'top_n_holdings': 'İlk N Varlık',
        'stock_symbol': 'Hisse Senedi Sembolü',
        'select_funds': 'Kontrol Edilecek Fonları Seçin',
        'holdings_count': 'Gösterilen Toplam Varlık',
        'total_weight': 'Toplam Ağırlık',
        'top3_concentration': 'İlk 3 Konsantrasyon',
        'funds_holding': 'Tutan Fonlar',
        'max_weight': 'Maks Ağırlık',
        'avg_weight': 'Ort Ağırlık',
        'holdings_details': 'Varlık Detayları',
        'ownership_details': 'Sahiplik Detayları',

        # Macro Liquidity
        'macro_sankey_title': 'Makro Likidite Akış Sankey',
        'macro_sankey_subtitle': 'Küresel likidite akışlarını kaynaklardan risk varlıklarına görselleştirin',
        'liquidity_sources': 'Likidite Kaynakları',
        'include_m2': 'M2\'yi Dahil Et',
        'm2_weight': 'M2 Ağırlığı',
        'include_cb': 'Merkez Bankası Bilançolarını Dahil Et',
        'cb_weight': 'MB Bilançosu Ağırlığı',
        'include_gli': 'Küresel Likidite Endeksini Dahil Et',
        'gli_weight': 'GLI Ağırlığı',
        'asset_allocations': 'Varlık Tahsisleri',
        'equities_allocation': 'Hisse Senedi Tahsisi',
        'btc_allocation': 'Bitcoin Tahsisi',
        'gold_allocation': 'Altın Tahsisi',
        'liquidity_overview': 'Likidite Genel Bakış',
        'total_liquidity_score': 'Toplam Likidite Skoru',
        'total_asset_allocation': 'Toplam Varlık Tahsisi',
        'sources_active': 'Aktif Kaynaklar',
        'asset_classes': 'Varlık Sınıfları',
        'liquidity_flow_viz': 'Likidite Akış Görselleştirmesi',
        'insights': 'İçgörüler',
        'about_macro': 'Makro Likidite Hakkında',

        # Export
        'export_options': 'Dışa Aktarma Seçenekleri',
        'download_png': 'PNG İndir',
        'download_html': 'HTML İndir',
        'download_csv': 'CSV İndir',

        # Messages
        'no_data_found': '{ticker} için finansal veri bulunamadı. Lütfen sembolü kontrol edip tekrar deneyin.',
        'try_tickers': 'Yaygın semboller: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA',
        'no_holdings_found': '{symbol} için varlık verisi bulunamadı',
        'try_funds': 'Popüler ETF\'ler: SPY, QQQ, VOO, ARKK, VT, IWM, VTI',
        'select_at_least_one_fund': 'Lütfen kontrol için en az bir fon seçin',
        'select_liquidity_source': 'Lütfen en az bir likidite kaynağı seçin',
        'set_asset_allocation': 'Lütfen en az bir varlık tahsisini > 0 yapın',
        'data_cached': 'Veri kaynakları: FMP, Alpha Vantage, Yahoo Finance | Performans için önbelleğe alınmış',
    }
}


class I18n:
    """Simple internationalization helper."""

    def __init__(self, default_language: str = 'en'):
        self.language = default_language

    def set_language(self, language: str):
        """Set current language."""
        if language in TRANSLATIONS:
            self.language = language
        else:
            raise ValueError(f"Language '{language}' not supported")

    def t(self, key: str, **kwargs) -> str:
        """
        Translate a key to current language.

        Args:
            key: Translation key
            **kwargs: Variables to format into translation

        Returns:
            Translated string
        """
        translations = TRANSLATIONS.get(self.language, TRANSLATIONS['en'])
        text = translations.get(key, key)

        # Format with variables if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass

        return text

    def __call__(self, key: str, **kwargs) -> str:
        """Shorthand for translate."""
        return self.t(key, **kwargs)


# Global instance
_i18n = I18n()


def get_i18n() -> I18n:
    """Get global i18n instance."""
    return _i18n


def t(key: str, **kwargs) -> str:
    """Module-level translate function."""
    return _i18n.t(key, **kwargs)


def set_language(language: str):
    """Module-level set language function."""
    _i18n.set_language(language)


def get_available_languages() -> list:
    """Get list of available languages."""
    return list(TRANSLATIONS.keys())
