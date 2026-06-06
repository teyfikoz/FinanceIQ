from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

try:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


class PublicPricePredictionEngine:
    def __init__(self, symbol: str, period: str = "2y"):
        self.symbol = symbol.upper()
        self.period = period
        self.data: pd.DataFrame | None = None

    def fetch_data(self) -> bool:
        try:
            ticker = yf.Ticker(self.symbol)
            self.data = ticker.history(period=self.period)
            if self.data is None or self.data.empty:
                return False
            self.data = self._add_technical_indicators(self.data)
            return not self.data.empty
        except Exception:
            return False

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        enriched = df.copy()
        enriched["SMA_20"] = enriched["Close"].rolling(window=20).mean()
        enriched["SMA_50"] = enriched["Close"].rolling(window=50).mean()
        enriched["EMA_12"] = enriched["Close"].ewm(span=12, adjust=False).mean()
        enriched["EMA_26"] = enriched["Close"].ewm(span=26, adjust=False).mean()
        enriched["MACD"] = enriched["EMA_12"] - enriched["EMA_26"]
        delta = enriched["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        enriched["RSI"] = 100 - (100 / (1 + rs))
        enriched["Volume_SMA"] = enriched["Volume"].rolling(window=20).mean()
        enriched["Momentum"] = enriched["Close"] - enriched["Close"].shift(10)
        enriched["ROC"] = ((enriched["Close"] - enriched["Close"].shift(10)) / enriched["Close"].shift(10)) * 100
        return enriched.dropna()

    def linear_regression_prediction(self, days: int = 30) -> Optional[Dict[str, Any]]:
        if not HAS_SKLEARN or self.data is None:
            return None
        df = self.data.copy()
        df["Days"] = np.arange(len(df))
        train_size = int(len(df) * 0.8)
        train = df[:train_size]
        test = df[train_size:]
        model = LinearRegression()
        model.fit(train[["Days"]].values, train["Close"].values)
        test_pred = model.predict(test[["Days"]].values)
        mse = mean_squared_error(test["Close"].values, test_pred)
        mae = mean_absolute_error(test["Close"].values, test_pred)
        r2 = r2_score(test["Close"].values, test_pred)
        last_day = int(df["Days"].iloc[-1])
        future_days = np.arange(last_day + 1, last_day + days + 1).reshape(-1, 1)
        future_pred = model.predict(future_days)
        future_dates = pd.date_range(start=df.index[-1] + timedelta(days=1), periods=days)
        return {
            "model_name": "Linear Regression",
            "predictions": future_pred,
            "dates": future_dates,
            "metrics": {"RMSE": np.sqrt(mse), "MAE": mae, "R²": r2},
        }

    def random_forest_prediction(self, days: int = 30) -> Optional[Dict[str, Any]]:
        if not HAS_SKLEARN or self.data is None:
            return None
        df = self.data.copy()
        features = [column for column in ["SMA_20", "SMA_50", "RSI", "MACD", "Volume_SMA", "Momentum", "ROC"] if column in df.columns]
        if not features:
            return None
        X = df[features].values
        y = df["Close"].values
        train_size = int(len(df) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        test_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, test_pred)
        mae = mean_absolute_error(y_test, test_pred)
        r2 = r2_score(y_test, test_pred)
        last_features = X[-1].reshape(1, -1)
        future_pred = []
        for _ in range(days):
            prediction = float(model.predict(last_features)[0])
            future_pred.append(prediction)
        future_dates = pd.date_range(start=df.index[-1] + timedelta(days=1), periods=days)
        return {
            "model_name": "Random Forest",
            "predictions": np.array(future_pred),
            "dates": future_dates,
            "metrics": {"RMSE": np.sqrt(mse), "MAE": mae, "R²": r2},
        }

    def gradient_boosting_prediction(self, days: int = 30) -> Optional[Dict[str, Any]]:
        if not HAS_SKLEARN or self.data is None:
            return None
        df = self.data.copy()
        features = [column for column in ["SMA_20", "SMA_50", "RSI", "MACD", "Volume_SMA", "Momentum"] if column in df.columns]
        if not features:
            return None
        X = df[features].values
        y = df["Close"].values
        train_size = int(len(df) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
        model.fit(X_train, y_train)
        test_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, test_pred)
        mae = mean_absolute_error(y_test, test_pred)
        r2 = r2_score(y_test, test_pred)
        last_features = X[-1].reshape(1, -1)
        future_pred = []
        for _ in range(days):
            prediction = float(model.predict(last_features)[0])
            future_pred.append(prediction)
        future_dates = pd.date_range(start=df.index[-1] + timedelta(days=1), periods=days)
        return {
            "model_name": "Gradient Boosting",
            "predictions": np.array(future_pred),
            "dates": future_dates,
            "metrics": {"RMSE": np.sqrt(mse), "MAE": mae, "R²": r2},
        }

    def arima_prediction(self, days: int = 30, order: Tuple[int, int, int] = (5, 1, 0)) -> Optional[Dict[str, Any]]:
        if not HAS_STATSMODELS or self.data is None:
            return None
        prices = self.data["Close"].values
        train_size = int(len(prices) * 0.8)
        train, test = prices[:train_size], prices[train_size:]
        fitted_model = ARIMA(train, order=order).fit()
        test_pred = fitted_model.forecast(steps=len(test))
        mse = mean_squared_error(test, test_pred)
        mae = mean_absolute_error(test, test_pred)
        fitted_full = ARIMA(prices, order=order).fit()
        future_pred = fitted_full.forecast(steps=days)
        future_dates = pd.date_range(start=self.data.index[-1] + timedelta(days=1), periods=days)
        return {
            "model_name": f"ARIMA{order}",
            "predictions": future_pred,
            "dates": future_dates,
            "metrics": {"RMSE": np.sqrt(mse), "MAE": mae, "AIC": fitted_full.aic},
        }

    def monte_carlo_simulation(self, days: int = 30, simulations: int = 1000) -> Optional[Dict[str, Any]]:
        if self.data is None:
            return None
        returns = self.data["Close"].pct_change().dropna()
        mean_return = returns.mean()
        std_return = returns.std()
        last_price = float(self.data["Close"].iloc[-1])
        simulation_results = np.zeros((simulations, days))
        for i in range(simulations):
            price = last_price
            for j in range(days):
                price = price * (1 + np.random.normal(mean_return, std_return))
                simulation_results[i, j] = price
        future_dates = pd.date_range(start=self.data.index[-1] + timedelta(days=1), periods=days)
        return {
            "model_name": f"Monte Carlo ({simulations} sims)",
            "predictions": np.percentile(simulation_results, 50, axis=0),
            "dates": future_dates,
            "metrics": {"Mean Return": mean_return, "Std Return": std_return},
        }

    def get_all_predictions(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        if not self.fetch_data():
            return {}
        results: Dict[str, Dict[str, Any]] = {}
        models = [
            ("Linear Regression", lambda: self.linear_regression_prediction(days)),
            ("Random Forest", lambda: self.random_forest_prediction(days)),
            ("Gradient Boosting", lambda: self.gradient_boosting_prediction(days)),
            ("ARIMA", lambda: self.arima_prediction(days)),
            ("Monte Carlo", lambda: self.monte_carlo_simulation(days)),
        ]
        for name, runner in models:
            try:
                result = runner()
                if result:
                    results[name] = result
            except Exception:
                continue
        return results
