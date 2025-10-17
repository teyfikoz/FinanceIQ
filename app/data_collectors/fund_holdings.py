"""
Fund Holdings Data Collector
Fonların hisse dağılımları ve hisse-fon analizi için veri toplayıcı
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
import time
import json
from bs4 import BeautifulSoup

from .base import BaseCollector
from app.core.config import settings


class FundHoldingsCollector(BaseCollector):
    """Fund holdings ve hisse-fon analizi için veri toplayıcı."""

    def __init__(self):
        super().__init__("fund_holdings")
        self.rate_limit_delay = 1.0

        # Popüler ETF'ler ve fonlar
        self.popular_etfs = {
            # Broad Market ETFs
            "SPY": "SPDR S&P 500 ETF Trust",
            "QQQ": "Invesco QQQ Trust",
            "IWM": "iShares Russell 2000 ETF",
            "VTI": "Vanguard Total Stock Market ETF",
            "VOO": "Vanguard S&P 500 ETF",
            "VEA": "Vanguard FTSE Developed Markets ETF",
            "VWO": "Vanguard FTSE Emerging Markets ETF",

            # Sector ETFs
            "XLK": "Technology Select Sector SPDR Fund",
            "XLF": "Financial Select Sector SPDR Fund",
            "XLE": "Energy Select Sector SPDR Fund",
            "XLV": "Health Care Select Sector SPDR Fund",
            "XLI": "Industrial Select Sector SPDR Fund",
            "XLY": "Consumer Discretionary Select Sector SPDR Fund",
            "XLP": "Consumer Staples Select Sector SPDR Fund",
            "XLU": "Utilities Select Sector SPDR Fund",
            "XLB": "Materials Select Sector SPDR Fund",
            "XLRE": "Real Estate Select Sector SPDR Fund",

            # International
            "EEM": "iShares MSCI Emerging Markets ETF",
            "EFA": "iShares MSCI EAFE ETF",
            "FXI": "iShares China Large-Cap ETF",
            "EWJ": "iShares MSCI Japan ETF",
            "EWG": "iShares MSCI Germany ETF",

            # Bonds
            "TLT": "iShares 20+ Year Treasury Bond ETF",
            "AGG": "iShares Core U.S. Aggregate Bond ETF",
            "LQD": "iShares iBoxx $ Investment Grade Corporate Bond ETF",
            "HYG": "iShares iBoxx $ High Yield Corporate Bond ETF",

            # Commodities & Gold
            "GLD": "SPDR Gold Shares",
            "SLV": "iShares Silver Trust",
            "USO": "United States Oil Fund",
            "DBA": "Invesco DB Agriculture Fund",
            "DBC": "Invesco DB Commodity Index Tracking Fund",

            # Growth/Innovation
            "ARKK": "ARK Innovation ETF",
            "ARKQ": "ARK Autonomous Technology & Robotics ETF",
            "ARKW": "ARK Next Generation Internet ETF",
            "VGT": "Vanguard Information Technology ETF",
            "VUG": "Vanguard Growth ETF",

            # Dividend
            "VYM": "Vanguard High Dividend Yield ETF",
            "SCHD": "Schwab US Dividend Equity ETF",
            "DVY": "iShares Select Dividend ETF",

            # Small/Mid Cap
            "IJH": "iShares Core S&P Mid-Cap ETF",
            "IJR": "iShares Core S&P Small-Cap ETF",
            "VB": "Vanguard Small-Cap ETF",
            "VO": "Vanguard Mid-Cap ETF"
        }

        # Global hisse senetleri
        self.global_stocks = {
            # Tech Giants
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "GOOGL": "Alphabet Inc.",
            "AMZN": "Amazon.com Inc.",
            "TSLA": "Tesla Inc.",
            "META": "Meta Platforms Inc.",
            "NVDA": "NVIDIA Corporation",
            "NFLX": "Netflix Inc.",
            "ADBE": "Adobe Inc.",
            "CRM": "Salesforce Inc.",

            # Banks & Finance
            "JPM": "JPMorgan Chase & Co.",
            "BAC": "Bank of America Corp.",
            "WFC": "Wells Fargo & Company",
            "GS": "Goldman Sachs Group Inc.",
            "MS": "Morgan Stanley",
            "V": "Visa Inc.",
            "MA": "Mastercard Inc.",
            "AXP": "American Express Company",

            # Healthcare
            "JNJ": "Johnson & Johnson",
            "PFE": "Pfizer Inc.",
            "UNH": "UnitedHealth Group Inc.",
            "ABT": "Abbott Laboratories",
            "TMO": "Thermo Fisher Scientific Inc.",
            "MDT": "Medtronic plc",

            # Consumer
            "KO": "The Coca-Cola Company",
            "PG": "Procter & Gamble Co.",
            "WMT": "Walmart Inc.",
            "DIS": "The Walt Disney Company",
            "MCD": "McDonald's Corporation",
            "NKE": "Nike Inc.",

            # Energy
            "XOM": "Exxon Mobil Corporation",
            "CVX": "Chevron Corporation",
            "COP": "ConocoPhillips",

            # Industrial
            "BA": "Boeing Company",
            "CAT": "Caterpillar Inc.",
            "GE": "General Electric Company",
            "MMM": "3M Company",

            # Turkish Stocks
            "THYAO.IS": "Turkish Airlines",
            "AKBNK.IS": "Akbank",
            "GARAN.IS": "Garanti BBVA",
            "SISE.IS": "Şişecam",
            "TCELL.IS": "Turkcell",
            "TUPRS.IS": "Tüpraş",
            "ARCLK.IS": "Arçelik",
            "BIMAS.IS": "BIM",
            "KRDMD.IS": "Kardemir",
            "PETKM.IS": "Petkim"
        }

    def fetch_etf_holdings_yf(self, symbol: str) -> Dict[str, Any]:
        """Yahoo Finance'dan ETF holdings çek."""
        try:
            ticker = yf.Ticker(symbol)

            # ETF info
            info = ticker.info

            # Holdings bilgilerini al (yfinance sınırlı holdings sağlar)
            holdings_data = []

            # Ticker'dan holdings bilgilerini çek
            try:
                # Yahoo Finance API'sinden holdings çekmek için alternatif yöntem
                holdings = ticker.institutional_holders
                if holdings is not None and not holdings.empty:
                    for _, row in holdings.head(10).iterrows():
                        holdings_data.append({
                            "holder": row.get("Holder", "Unknown"),
                            "shares": row.get("Shares", 0),
                            "date_reported": row.get("Date Reported", ""),
                            "percent_out": row.get("% Out", 0)
                        })
            except:
                pass

            # Major holders bilgisi
            major_holders = []
            try:
                mh = ticker.major_holders
                if mh is not None and not mh.empty:
                    major_holders = mh.to_dict('records')
            except:
                pass

            # Top holdings için alternatif yöntem (sector allocation)
            sector_data = []
            try:
                # Mutual fund holders (ETF için holdings proxy)
                fund_holders = ticker.mutualfund_holders
                if fund_holders is not None and not fund_holders.empty:
                    for _, row in fund_holders.head(15).iterrows():
                        holdings_data.append({
                            "holder": row.get("Holder", "Unknown"),
                            "shares": row.get("Shares", 0),
                            "date_reported": row.get("Date Reported", ""),
                            "percent_out": row.get("% Out", 0)
                        })
            except:
                pass

            result = {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "fund_type": "ETF",
                "total_assets": info.get("totalAssets"),
                "expense_ratio": info.get("annualReportExpenseRatio"),
                "holdings": holdings_data,
                "major_holders": major_holders,
                "sector_allocation": sector_data,
                "last_updated": datetime.utcnow().isoformat(),
                "data_source": "yahoo_finance"
            }

            self.logger.info(f"Successfully fetched ETF holdings for {symbol}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to fetch ETF holdings for {symbol}", error=str(e))
            return {"error": str(e)}

    def fetch_stock_in_funds(self, stock_symbol: str, fund_list: List[str] = None) -> Dict[str, Any]:
        """Bir hisse senedinin hangi fonlarda yer aldığını bul."""
        try:
            if fund_list is None:
                fund_list = list(self.popular_etfs.keys())[:20]  # İlk 20 ETF

            stock_in_funds = []
            total_funds_checked = 0
            funds_containing_stock = 0

            for fund_symbol in fund_list:
                total_funds_checked += 1
                try:
                    # Fund holdings çek
                    fund_data = self.fetch_etf_holdings_yf(fund_symbol)

                    if "error" not in fund_data and "holdings" in fund_data:
                        # Holdings içinde stock'u ara
                        for holding in fund_data["holdings"]:
                            holder_name = holding.get("holder", "").upper()
                            stock_name = self.global_stocks.get(stock_symbol, stock_symbol).upper()

                            # Basit string matching (geliştirilmesi gerekebilir)
                            if (stock_symbol.replace(".IS", "").upper() in holder_name or
                                stock_name in holder_name):

                                funds_containing_stock += 1
                                stock_in_funds.append({
                                    "fund_symbol": fund_symbol,
                                    "fund_name": self.popular_etfs.get(fund_symbol, fund_symbol),
                                    "weight_percent": holding.get("percent_out", 0),
                                    "shares": holding.get("shares", 0),
                                    "date_reported": holding.get("date_reported", ""),
                                    "holder_info": holder_name
                                })
                                break

                    time.sleep(self.rate_limit_delay)

                except Exception as e:
                    self.logger.warning(f"Error checking {fund_symbol} for {stock_symbol}: {e}")
                    continue

            # Sonuçları weight'e göre sırala
            stock_in_funds.sort(key=lambda x: x.get("weight_percent", 0), reverse=True)

            result = {
                "stock_symbol": stock_symbol,
                "stock_name": self.global_stocks.get(stock_symbol, stock_symbol),
                "funds_containing_stock": stock_in_funds,
                "total_funds_checked": total_funds_checked,
                "funds_containing_count": funds_containing_stock,
                "max_weight_percent": max([f.get("weight_percent", 0) for f in stock_in_funds]) if stock_in_funds else 0,
                "last_updated": datetime.utcnow().isoformat(),
                "data_source": "yahoo_finance"
            }

            self.logger.info(f"Found {funds_containing_stock} funds containing {stock_symbol}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to fetch stock in funds for {stock_symbol}", error=str(e))
            return {"error": str(e)}

    def get_fund_performance_comparison(self, fund_symbols: List[str], period: str = "6mo") -> Dict[str, Any]:
        """Fonların performans karşılaştırması."""
        try:
            performance_data = {}

            for symbol in fund_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=period)

                    if not hist.empty:
                        start_price = hist['Close'].iloc[0]
                        end_price = hist['Close'].iloc[-1]
                        total_return = ((end_price - start_price) / start_price) * 100

                        volatility = hist['Close'].pct_change().std() * np.sqrt(252) * 100

                        performance_data[symbol] = {
                            "name": self.popular_etfs.get(symbol, symbol),
                            "total_return": total_return,
                            "volatility": volatility,
                            "current_price": end_price,
                            "start_price": start_price,
                            "sharpe_ratio": total_return / volatility if volatility > 0 else 0
                        }

                except Exception as e:
                    self.logger.warning(f"Error getting performance for {symbol}: {e}")
                    continue

            result = {
                "performance_comparison": performance_data,
                "period": period,
                "best_performer": max(performance_data.items(), key=lambda x: x[1]["total_return"])[0] if performance_data else None,
                "lowest_volatility": min(performance_data.items(), key=lambda x: x[1]["volatility"])[0] if performance_data else None,
                "highest_sharpe": max(performance_data.items(), key=lambda x: x[1]["sharpe_ratio"])[0] if performance_data else None,
                "last_updated": datetime.utcnow().isoformat()
            }

            return result

        except Exception as e:
            self.logger.error("Failed to get fund performance comparison", error=str(e))
            return {"error": str(e)}

    def get_sector_analysis(self, symbol: str) -> Dict[str, Any]:
        """ETF/Fund sektör analizi."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Sektör bilgilerini al
            sector_data = {}

            # Info'dan sektör bilgilerini çıkar
            if 'sectorWeightings' in info:
                sector_data = info['sectorWeightings']

            result = {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "sector_breakdown": sector_data,
                "top_sectors": sorted(sector_data.items(), key=lambda x: x[1], reverse=True)[:5] if sector_data else [],
                "last_updated": datetime.utcnow().isoformat()
            }

            return result

        except Exception as e:
            self.logger.error(f"Failed to get sector analysis for {symbol}", error=str(e))
            return {"error": str(e)}

    def search_funds_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, str]]:
        """Kriterlere göre fon arama."""
        try:
            results = []

            # Kriter tipleri
            sector = criteria.get("sector", "").lower()
            fund_type = criteria.get("type", "").lower()
            region = criteria.get("region", "").lower()
            query = criteria.get("query", "").lower()

            for symbol, name in self.popular_etfs.items():
                name_lower = name.lower()
                symbol_lower = symbol.lower()

                match = True

                # Sektör filtresi
                if sector and sector not in name_lower:
                    match = False

                # Tip filtresi
                if fund_type:
                    if fund_type == "sector" and "select sector" not in name_lower:
                        match = False
                    elif fund_type == "international" and "international" not in name_lower and "emerging" not in name_lower:
                        match = False
                    elif fund_type == "bond" and "bond" not in name_lower and "treasury" not in name_lower:
                        match = False

                # Bölge filtresi
                if region:
                    if region == "us" and any(x in name_lower for x in ["emerging", "international", "china", "japan"]):
                        match = False
                    elif region == "international" and not any(x in name_lower for x in ["emerging", "international", "eafe"]):
                        match = False

                # Genel arama
                if query and query not in name_lower and query not in symbol_lower:
                    match = False

                if match:
                    results.append({
                        "symbol": symbol,
                        "name": name,
                        "type": "ETF"
                    })

            return results[:20]  # İlk 20 sonuç

        except Exception as e:
            self.logger.error("Failed to search funds", error=str(e))
            return []

    def collect_data(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Ana veri toplama fonksiyonu."""
        if symbols is None:
            # Default: Top 10 ETF
            symbols = list(self.popular_etfs.keys())[:10]

        try:
            fund_data = {}

            for symbol in symbols:
                holdings_data = self.fetch_etf_holdings_yf(symbol)
                if "error" not in holdings_data:
                    fund_data[symbol] = holdings_data

                time.sleep(self.rate_limit_delay)

            result = {
                "fund_holdings_data": fund_data,
                "total_funds": len(symbols),
                "successful_funds": len(fund_data),
                "last_updated": datetime.utcnow().isoformat()
            }

            return result

        except Exception as e:
            self.logger.error("Failed to collect fund holdings data", error=str(e))
            return {"error": str(e)}

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Veri doğrulama."""
        if not super().validate_data(data):
            return False

        # Fund holdings data kontrolü
        if "fund_holdings_data" in data:
            if not data["fund_holdings_data"]:
                self.logger.warning("No fund holdings data found")
                return False

        return True