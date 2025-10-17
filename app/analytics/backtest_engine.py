#!/usr/bin/env python3
"""
Backtest ve Strateji Test Motoru
Alım-satım stratejilerini geçmiş verilerle test etme
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class BacktestEngine:
    """Backtest ve strateji test motoru"""

    def __init__(self, symbol: str, start_date: str, end_date: str, initial_capital: float = 10000):
        """
        Args:
            symbol: Hisse senedi sembolü
            start_date: Başlangıç tarihi (YYYY-MM-DD)
            end_date: Bitiş tarihi (YYYY-MM-DD)
            initial_capital: Başlangıç sermayesi
        """
        self.symbol = symbol.upper()
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.data = self._fetch_data()

    def _fetch_data(self) -> pd.DataFrame:
        """Fiyat verilerini çek"""
        try:
            stock = yf.Ticker(self.symbol)
            df = stock.history(start=self.start_date, end=self.end_date)

            if df.empty:
                raise ValueError("No data available")

            return df

        except Exception as e:
            raise ValueError(f"Failed to fetch data: {str(e)}")

    def backtest_strategy(self, strategy: str, **params) -> Dict[str, Any]:
        """
        Strateji backtest'i

        Args:
            strategy: Strateji adı
                - 'sma_crossover': Hareketli ortalama kesişimi
                - 'rsi': RSI tabanlı
                - 'macd': MACD tabanlı
                - 'bollinger': Bollinger Bands
                - 'buy_hold': Al-tut stratejisi
            **params: Strateji parametreleri
        """
        if strategy == 'sma_crossover':
            return self._backtest_sma_crossover(**params)
        elif strategy == 'rsi':
            return self._backtest_rsi(**params)
        elif strategy == 'macd':
            return self._backtest_macd(**params)
        elif strategy == 'bollinger':
            return self._backtest_bollinger(**params)
        elif strategy == 'buy_hold':
            return self._backtest_buy_hold()
        else:
            return {"error": f"Unknown strategy: {strategy}"}

    def _backtest_sma_crossover(self, fast_period: int = 50, slow_period: int = 200) -> Dict[str, Any]:
        """SMA Crossover stratejisi"""
        df = self.data.copy()

        # Moving averages
        df['SMA_Fast'] = df['Close'].rolling(window=fast_period).mean()
        df['SMA_Slow'] = df['Close'].rolling(window=slow_period).mean()

        # Signals
        df['Signal'] = 0
        df.loc[df['SMA_Fast'] > df['SMA_Slow'], 'Signal'] = 1
        df['Position'] = df['Signal'].diff()

        # Execute trades
        trades = self._execute_trades(df)

        # Calculate performance
        performance = self._calculate_performance(trades, df)

        return {
            "strategy": "SMA Crossover",
            "parameters": {"fast_period": fast_period, "slow_period": slow_period},
            "trades": trades,
            "performance": performance,
            "equity_curve": self._generate_equity_curve(trades, df)
        }

    def _backtest_rsi(self, period: int = 14, oversold: int = 30, overbought: int = 70) -> Dict[str, Any]:
        """RSI stratejisi"""
        df = self.data.copy()

        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Signals
        df['Signal'] = 0
        df.loc[df['RSI'] < oversold, 'Signal'] = 1  # Buy
        df.loc[df['RSI'] > overbought, 'Signal'] = -1  # Sell

        # Execute trades
        trades = self._execute_trades(df)

        # Calculate performance
        performance = self._calculate_performance(trades, df)

        return {
            "strategy": "RSI",
            "parameters": {"period": period, "oversold": oversold, "overbought": overbought},
            "trades": trades,
            "performance": performance,
            "equity_curve": self._generate_equity_curve(trades, df)
        }

    def _backtest_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Any]:
        """MACD stratejisi"""
        df = self.data.copy()

        # Calculate MACD
        df['EMA_Fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = df['EMA_Fast'] - df['EMA_Slow']
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()

        # Signals
        df['Signal'] = 0
        df.loc[df['MACD'] > df['MACD_Signal'], 'Signal'] = 1
        df['Position'] = df['Signal'].diff()

        # Execute trades
        trades = self._execute_trades(df)

        # Calculate performance
        performance = self._calculate_performance(trades, df)

        return {
            "strategy": "MACD",
            "parameters": {"fast": fast, "slow": slow, "signal": signal},
            "trades": trades,
            "performance": performance,
            "equity_curve": self._generate_equity_curve(trades, df)
        }

    def _backtest_bollinger(self, period: int = 20, std_dev: float = 2.0) -> Dict[str, Any]:
        """Bollinger Bands stratejisi"""
        df = self.data.copy()

        # Calculate Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=period).mean()
        bb_std = df['Close'].rolling(window=period).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * std_dev)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * std_dev)

        # Signals
        df['Signal'] = 0
        df.loc[df['Close'] < df['BB_Lower'], 'Signal'] = 1  # Buy at lower band
        df.loc[df['Close'] > df['BB_Upper'], 'Signal'] = -1  # Sell at upper band

        # Execute trades
        trades = self._execute_trades(df)

        # Calculate performance
        performance = self._calculate_performance(trades, df)

        return {
            "strategy": "Bollinger Bands",
            "parameters": {"period": period, "std_dev": std_dev},
            "trades": trades,
            "performance": performance,
            "equity_curve": self._generate_equity_curve(trades, df)
        }

    def _backtest_buy_hold(self) -> Dict[str, Any]:
        """Buy and Hold stratejisi (benchmark)"""
        df = self.data.copy()

        # Single buy at start, hold till end
        buy_price = df['Close'].iloc[0]
        sell_price = df['Close'].iloc[-1]
        shares = self.initial_capital / buy_price

        total_return = (sell_price - buy_price) / buy_price * 100
        final_value = shares * sell_price

        return {
            "strategy": "Buy and Hold",
            "parameters": {},
            "trades": [{
                "type": "BUY",
                "date": df.index[0].strftime('%Y-%m-%d'),
                "price": float(buy_price),
                "shares": float(shares)
            }, {
                "type": "SELL",
                "date": df.index[-1].strftime('%Y-%m-%d'),
                "price": float(sell_price),
                "shares": float(shares)
            }],
            "performance": {
                "total_return": float(total_return),
                "final_value": float(final_value),
                "profit": float(final_value - self.initial_capital),
                "number_of_trades": 1
            },
            "equity_curve": [
                {"date": df.index[0].strftime('%Y-%m-%d'), "equity": self.initial_capital},
                {"date": df.index[-1].strftime('%Y-%m-%d'), "equity": final_value}
            ]
        }

    def _execute_trades(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """İşlemleri simüle et"""
        trades = []
        position = None  # None, 'long', 'short'
        shares = 0
        cash = self.initial_capital

        for idx, row in df.iterrows():
            # Buy signal
            if 'Position' in df.columns:
                signal = row['Position']
            else:
                signal = row['Signal']

            if signal == 1 and position is None:  # Buy
                shares = cash / row['Close']
                cash = 0
                position = 'long'
                trades.append({
                    "type": "BUY",
                    "date": idx.strftime('%Y-%m-%d'),
                    "price": float(row['Close']),
                    "shares": float(shares),
                    "value": float(shares * row['Close'])
                })

            elif signal == -1 and position == 'long':  # Sell
                cash = shares * row['Close']
                profit = cash - self.initial_capital
                position = None
                trades.append({
                    "type": "SELL",
                    "date": idx.strftime('%Y-%m-%d'),
                    "price": float(row['Close']),
                    "shares": float(shares),
                    "value": float(cash),
                    "profit": float(profit)
                })
                shares = 0

        # Close position if still open
        if position == 'long' and shares > 0:
            final_price = df['Close'].iloc[-1]
            cash = shares * final_price
            trades.append({
                "type": "SELL",
                "date": df.index[-1].strftime('%Y-%m-%d'),
                "price": float(final_price),
                "shares": float(shares),
                "value": float(cash),
                "profit": float(cash - self.initial_capital)
            })

        return trades

    def _calculate_performance(self, trades: List[Dict[str, Any]], df: pd.DataFrame) -> Dict[str, Any]:
        """Performans metriklerini hesapla"""
        if not trades:
            return {"error": "No trades executed"}

        # Final value
        final_trade = trades[-1]
        final_value = final_trade.get('value', self.initial_capital)

        # Total return
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100

        # Number of trades
        buy_trades = [t for t in trades if t['type'] == 'BUY']
        sell_trades = [t for t in trades if t['type'] == 'SELL']
        num_trades = len(buy_trades)

        # Win rate
        winning_trades = sum(1 for t in sell_trades if t.get('profit', 0) > 0)
        win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0

        # Average profit/loss
        profits = [t.get('profit', 0) for t in sell_trades if 'profit' in t]
        avg_profit = np.mean(profits) if profits else 0
        max_profit = max(profits) if profits else 0
        max_loss = min(profits) if profits else 0

        # Max drawdown
        max_drawdown = self._calculate_max_drawdown(trades, df)

        # Sharpe ratio (simplified)
        returns = [t.get('profit', 0) / self.initial_capital for t in sell_trades if 'profit' in t]
        sharpe_ratio = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if len(returns) > 1 and np.std(returns) > 0 else 0

        return {
            "initial_capital": self.initial_capital,
            "final_value": float(final_value),
            "total_return": float(total_return),
            "total_profit": float(final_value - self.initial_capital),
            "number_of_trades": num_trades,
            "winning_trades": winning_trades,
            "losing_trades": len(sell_trades) - winning_trades,
            "win_rate": float(win_rate),
            "avg_profit_per_trade": float(avg_profit),
            "max_profit": float(max_profit),
            "max_loss": float(max_loss),
            "max_drawdown": float(max_drawdown),
            "sharpe_ratio": float(sharpe_ratio)
        }

    def _calculate_max_drawdown(self, trades: List[Dict[str, Any]], df: pd.DataFrame) -> float:
        """Maksimum düşüş (drawdown) hesapla"""
        equity_curve = self._generate_equity_curve(trades, df)

        if not equity_curve:
            return 0.0

        equities = [e['equity'] for e in equity_curve]
        peak = equities[0]
        max_dd = 0

        for equity in equities:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            if dd > max_dd:
                max_dd = dd

        return float(max_dd)

    def _generate_equity_curve(self, trades: List[Dict[str, Any]], df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sermaye eğrisi oluştur"""
        if not trades:
            return []

        equity_curve = []
        cash = self.initial_capital
        shares = 0

        for trade in trades:
            if trade['type'] == 'BUY':
                shares = trade['shares']
                cash = 0
            elif trade['type'] == 'SELL':
                cash = trade['value']
                shares = 0

            equity = cash if cash > 0 else (shares * trade['price'])

            equity_curve.append({
                "date": trade['date'],
                "equity": float(equity)
            })

        return equity_curve

    def compare_strategies(self, strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Birden fazla stratejiyi karşılaştır"""
        results = []

        for strat in strategies:
            strategy_name = strat['name']
            params = strat.get('params', {})

            result = self.backtest_strategy(strategy_name, **params)
            if 'error' not in result:
                results.append({
                    "strategy": result['strategy'],
                    "performance": result['performance']
                })

        # Ranking
        if results:
            results.sort(key=lambda x: x['performance']['total_return'], reverse=True)

        return {
            "comparison": results,
            "best_strategy": results[0]['strategy'] if results else None,
            "best_return": results[0]['performance']['total_return'] if results else 0
        }

    def optimize_strategy(self, strategy: str, param_ranges: Dict[str, List]) -> Dict[str, Any]:
        """Strateji parametrelerini optimize et"""
        best_result = None
        best_return = float('-inf')
        all_results = []

        # Grid search
        if strategy == 'sma_crossover':
            for fast in param_ranges.get('fast_period', [20, 50]):
                for slow in param_ranges.get('slow_period', [100, 200]):
                    if fast < slow:
                        result = self._backtest_sma_crossover(fast, slow)
                        if 'performance' in result:
                            total_return = result['performance']['total_return']
                            all_results.append({
                                "params": {"fast": fast, "slow": slow},
                                "return": total_return
                            })
                            if total_return > best_return:
                                best_return = total_return
                                best_result = result

        elif strategy == 'rsi':
            for period in param_ranges.get('period', [10, 14, 20]):
                for oversold in param_ranges.get('oversold', [20, 30]):
                    for overbought in param_ranges.get('overbought', [70, 80]):
                        result = self._backtest_rsi(period, oversold, overbought)
                        if 'performance' in result:
                            total_return = result['performance']['total_return']
                            all_results.append({
                                "params": {"period": period, "oversold": oversold, "overbought": overbought},
                                "return": total_return
                            })
                            if total_return > best_return:
                                best_return = total_return
                                best_result = result

        return {
            "best_parameters": best_result['parameters'] if best_result else None,
            "best_performance": best_result['performance'] if best_result else None,
            "all_results": sorted(all_results, key=lambda x: x['return'], reverse=True)[:10]
        }
