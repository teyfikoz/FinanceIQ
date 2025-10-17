"""AI-Powered Stock Price Prediction Models"""
import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Try importing ML libraries
try:
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False


class StockPredictionEngine:
    """Comprehensive stock price prediction engine with multiple AI models"""

    def __init__(self, symbol: str, period: str = "2y"):
        """
        Initialize prediction engine

        Args:
            symbol: Stock ticker symbol
            period: Historical data period (1y, 2y, 5y, max)
        """
        self.symbol = symbol
        self.period = period
        self.data = None
        self.scaler = MinMaxScaler() if HAS_SKLEARN else None

    def fetch_data(self) -> bool:
        """Fetch historical stock data

        Returns:
            True if successful, False otherwise
        """
        try:
            ticker = yf.Ticker(self.symbol)
            self.data = ticker.history(period=self.period)

            if self.data.empty:
                return False

            # Add technical indicators
            self.data = self._add_technical_indicators(self.data)
            return True

        except Exception as e:
            print(f"Error fetching data: {str(e)}")
            return False

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataframe"""
        try:
            # Moving averages
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()

            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Bollinger Bands
            df['BB_middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
            df['BB_lower'] = df['BB_middle'] - (bb_std * 2)

            # Volume indicators
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()

            # Price momentum
            df['Momentum'] = df['Close'] - df['Close'].shift(10)

            # Rate of change
            df['ROC'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100

            return df.dropna()

        except Exception as e:
            print(f"Error adding indicators: {str(e)}")
            return df

    def linear_regression_prediction(self, days: int = 30) -> Optional[Dict]:
        """Linear Regression model prediction

        Args:
            days: Number of days to predict

        Returns:
            Dictionary with predictions and metrics
        """
        if not HAS_SKLEARN or self.data is None:
            return None

        try:
            # Prepare data
            df = self.data.copy()
            df['Days'] = np.arange(len(df))

            # Train-test split
            train_size = int(len(df) * 0.8)
            train = df[:train_size]
            test = df[train_size:]

            # Train model
            X_train = train[['Days']].values
            y_train = train['Close'].values

            model = LinearRegression()
            model.fit(X_train, y_train)

            # Test predictions
            X_test = test[['Days']].values
            y_test = test['Close'].values
            test_pred = model.predict(X_test)

            # Calculate metrics
            mse = mean_squared_error(y_test, test_pred)
            mae = mean_absolute_error(y_test, test_pred)
            r2 = r2_score(y_test, test_pred)

            # Future predictions
            last_day = df['Days'].iloc[-1]
            future_days = np.arange(last_day + 1, last_day + days + 1).reshape(-1, 1)
            future_pred = model.predict(future_days)

            # Create future dates
            last_date = df.index[-1]
            future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days)

            return {
                'model_name': 'Linear Regression',
                'predictions': future_pred,
                'dates': future_dates,
                'metrics': {
                    'RMSE': np.sqrt(mse),
                    'MAE': mae,
                    'R²': r2
                },
                'test_predictions': test_pred,
                'test_actual': y_test,
                'test_dates': test.index
            }

        except Exception as e:
            print(f"Linear Regression error: {str(e)}")
            return None

    def random_forest_prediction(self, days: int = 30) -> Optional[Dict]:
        """Random Forest model prediction with multiple features

        Args:
            days: Number of days to predict

        Returns:
            Dictionary with predictions and metrics
        """
        if not HAS_SKLEARN or self.data is None:
            return None

        try:
            df = self.data.copy()

            # Select features
            features = ['SMA_20', 'SMA_50', 'RSI', 'MACD', 'Volume_SMA', 'Momentum', 'ROC']
            available_features = [f for f in features if f in df.columns]

            if not available_features:
                return None

            # Prepare data
            df = df.dropna()
            X = df[available_features].values
            y = df['Close'].values

            # Train-test split
            train_size = int(len(df) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]

            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            model.fit(X_train, y_train)

            # Test predictions
            test_pred = model.predict(X_test)

            # Calculate metrics
            mse = mean_squared_error(y_test, test_pred)
            mae = mean_absolute_error(y_test, test_pred)
            r2 = r2_score(y_test, test_pred)

            # Future predictions - use last known values with trend
            last_features = X[-1].reshape(1, -1)
            future_pred = []

            for i in range(days):
                pred = model.predict(last_features)[0]
                future_pred.append(pred)

                # Update features for next prediction (simple approach)
                # In practice, you'd update technical indicators properly
                last_features = last_features.copy()

            # Create future dates
            last_date = df.index[-1]
            future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days)

            return {
                'model_name': 'Random Forest',
                'predictions': np.array(future_pred),
                'dates': future_dates,
                'metrics': {
                    'RMSE': np.sqrt(mse),
                    'MAE': mae,
                    'R²': r2
                },
                'test_predictions': test_pred,
                'test_actual': y_test,
                'test_dates': df.index[train_size:],
                'feature_importance': dict(zip(available_features, model.feature_importances_))
            }

        except Exception as e:
            print(f"Random Forest error: {str(e)}")
            return None

    def arima_prediction(self, days: int = 30, order: Tuple[int, int, int] = (5, 1, 0)) -> Optional[Dict]:
        """ARIMA model prediction

        Args:
            days: Number of days to predict
            order: ARIMA (p, d, q) parameters

        Returns:
            Dictionary with predictions and metrics
        """
        if not HAS_STATSMODELS or self.data is None:
            return None

        try:
            df = self.data.copy()
            prices = df['Close'].values

            # Train-test split
            train_size = int(len(prices) * 0.8)
            train, test = prices[:train_size], prices[train_size:]

            # Train model
            model = ARIMA(train, order=order)
            fitted_model = model.fit()

            # Test predictions
            test_pred = fitted_model.forecast(steps=len(test))

            # Calculate metrics
            mse = mean_squared_error(test, test_pred)
            mae = mean_absolute_error(test, test_pred)

            # Future predictions
            full_model = ARIMA(prices, order=order)
            fitted_full = full_model.fit()
            future_pred = fitted_full.forecast(steps=days)

            # Create future dates
            last_date = df.index[-1]
            future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days)

            return {
                'model_name': f'ARIMA{order}',
                'predictions': future_pred,
                'dates': future_dates,
                'metrics': {
                    'RMSE': np.sqrt(mse),
                    'MAE': mae,
                    'AIC': fitted_full.aic,
                    'BIC': fitted_full.bic
                },
                'test_predictions': test_pred,
                'test_actual': test,
                'test_dates': df.index[train_size:]
            }

        except Exception as e:
            print(f"ARIMA error: {str(e)}")
            return None

    def prophet_prediction(self, days: int = 30) -> Optional[Dict]:
        """Prophet model prediction (Facebook's forecasting tool)

        Args:
            days: Number of days to predict

        Returns:
            Dictionary with predictions and metrics
        """
        if not HAS_PROPHET or self.data is None:
            return None

        try:
            # Prepare data for Prophet
            df = self.data.reset_index()
            df_prophet = pd.DataFrame({
                'ds': df['Date'],
                'y': df['Close']
            })

            # Train-test split
            train_size = int(len(df_prophet) * 0.8)
            train = df_prophet[:train_size]
            test = df_prophet[train_size:]

            # Train model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05
            )
            model.fit(train)

            # Test predictions
            test_pred_df = model.predict(test[['ds']])
            test_pred = test_pred_df['yhat'].values
            test_actual = test['y'].values

            # Calculate metrics
            mse = mean_squared_error(test_actual, test_pred)
            mae = mean_absolute_error(test_actual, test_pred)

            # Future predictions
            full_model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05
            )
            full_model.fit(df_prophet)

            future = full_model.make_future_dataframe(periods=days)
            forecast = full_model.predict(future)

            # Get only future predictions
            future_pred = forecast.tail(days)

            return {
                'model_name': 'Prophet',
                'predictions': future_pred['yhat'].values,
                'dates': future_pred['ds'].values,
                'upper_bound': future_pred['yhat_upper'].values,
                'lower_bound': future_pred['yhat_lower'].values,
                'metrics': {
                    'RMSE': np.sqrt(mse),
                    'MAE': mae
                },
                'test_predictions': test_pred,
                'test_actual': test_actual,
                'test_dates': test['ds'].values,
                'full_forecast': forecast
            }

        except Exception as e:
            print(f"Prophet error: {str(e)}")
            return None

    def gradient_boosting_prediction(self, days: int = 30) -> Optional[Dict]:
        """Gradient Boosting model prediction

        Args:
            days: Number of days to predict

        Returns:
            Dictionary with predictions and metrics
        """
        if not HAS_SKLEARN or self.data is None:
            return None

        try:
            df = self.data.copy()

            # Select features
            features = ['SMA_20', 'SMA_50', 'RSI', 'MACD', 'Volume_SMA', 'Momentum']
            available_features = [f for f in features if f in df.columns]

            if not available_features:
                return None

            # Prepare data
            df = df.dropna()
            X = df[available_features].values
            y = df['Close'].values

            # Train-test split
            train_size = int(len(df) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]

            # Train model
            model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
            model.fit(X_train, y_train)

            # Test predictions
            test_pred = model.predict(X_test)

            # Calculate metrics
            mse = mean_squared_error(y_test, test_pred)
            mae = mean_absolute_error(y_test, test_pred)
            r2 = r2_score(y_test, test_pred)

            # Future predictions
            last_features = X[-1].reshape(1, -1)
            future_pred = []

            for i in range(days):
                pred = model.predict(last_features)[0]
                future_pred.append(pred)
                last_features = last_features.copy()

            # Create future dates
            last_date = df.index[-1]
            future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days)

            return {
                'model_name': 'Gradient Boosting',
                'predictions': np.array(future_pred),
                'dates': future_dates,
                'metrics': {
                    'RMSE': np.sqrt(mse),
                    'MAE': mae,
                    'R²': r2
                },
                'test_predictions': test_pred,
                'test_actual': y_test,
                'test_dates': df.index[train_size:]
            }

        except Exception as e:
            print(f"Gradient Boosting error: {str(e)}")
            return None

    def monte_carlo_simulation(self, days: int = 30, simulations: int = 1000) -> Optional[Dict]:
        """Monte Carlo simulation for price prediction

        Args:
            days: Number of days to simulate
            simulations: Number of simulation runs

        Returns:
            Dictionary with simulation results
        """
        if self.data is None:
            return None

        try:
            df = self.data.copy()
            returns = df['Close'].pct_change().dropna()

            # Calculate statistics
            mean_return = returns.mean()
            std_return = returns.std()
            last_price = df['Close'].iloc[-1]

            # Run simulations
            simulation_results = np.zeros((simulations, days))

            for i in range(simulations):
                prices = [last_price]
                for j in range(days):
                    # Generate random return
                    random_return = np.random.normal(mean_return, std_return)
                    new_price = prices[-1] * (1 + random_return)
                    prices.append(new_price)
                    simulation_results[i, j] = new_price

            # Calculate percentiles
            percentile_5 = np.percentile(simulation_results, 5, axis=0)
            percentile_25 = np.percentile(simulation_results, 25, axis=0)
            percentile_50 = np.percentile(simulation_results, 50, axis=0)
            percentile_75 = np.percentile(simulation_results, 75, axis=0)
            percentile_95 = np.percentile(simulation_results, 95, axis=0)

            # Create future dates
            last_date = df.index[-1]
            future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days)

            return {
                'model_name': f'Monte Carlo ({simulations} sims)',
                'predictions': percentile_50,
                'dates': future_dates,
                'percentile_5': percentile_5,
                'percentile_25': percentile_25,
                'percentile_75': percentile_75,
                'percentile_95': percentile_95,
                'all_simulations': simulation_results,
                'metrics': {
                    'Mean Return': mean_return,
                    'Std Return': std_return,
                    'Volatility (Annual)': std_return * np.sqrt(252)
                }
            }

        except Exception as e:
            print(f"Monte Carlo error: {str(e)}")
            return None

    def get_all_predictions(self, days: int = 30) -> Dict[str, Dict]:
        """Run all available prediction models

        Args:
            days: Number of days to predict

        Returns:
            Dictionary of all model results
        """
        results = {}

        if not self.fetch_data():
            return results

        # Run each model
        models = [
            ('Linear Regression', lambda: self.linear_regression_prediction(days)),
            ('Random Forest', lambda: self.random_forest_prediction(days)),
            ('Gradient Boosting', lambda: self.gradient_boosting_prediction(days)),
            ('ARIMA', lambda: self.arima_prediction(days)),
            ('Prophet', lambda: self.prophet_prediction(days)),
            ('Monte Carlo', lambda: self.monte_carlo_simulation(days))
        ]

        for name, model_func in models:
            try:
                result = model_func()
                if result:
                    results[name] = result
            except Exception as e:
                print(f"Error running {name}: {str(e)}")
                continue

        return results
