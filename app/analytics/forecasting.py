import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from app.utils.logger import get_logger


class ForecastingEngine:
    """Advanced forecasting engine for financial predictions."""

    def __init__(self):
        self.logger = get_logger("analytics.forecasting")
        self.models = {}
        self.scalers = {}

    def create_lstm_model(self, sequence_length: int = 60, features: int = 1) -> Any:
        """Create LSTM model for time series prediction."""
        try:
            import tensorflow as tf
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
            from tensorflow.keras.optimizers import Adam

            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(sequence_length, features)),
                Dropout(0.2),
                BatchNormalization(),

                LSTM(50, return_sequences=True),
                Dropout(0.2),
                BatchNormalization(),

                LSTM(50, return_sequences=False),
                Dropout(0.2),

                Dense(25),
                Dense(1)
            ])

            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mean_squared_error',
                metrics=['mae']
            )

            return model

        except ImportError:
            self.logger.warning("TensorFlow not available, using fallback model")
            return None

    def prepare_data_for_lstm(
        self,
        prices: pd.Series,
        sequence_length: int = 60
    ) -> Tuple[np.ndarray, np.ndarray, Any]:
        """Prepare data for LSTM training."""
        try:
            if not SKLEARN_AVAILABLE:
                raise ImportError("sklearn not available")

            # Scale the data
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(prices.values.reshape(-1, 1))

            # Create training sequences
            X, y = [], []

            for i in range(sequence_length, len(scaled_data)):
                X.append(scaled_data[i-sequence_length:i, 0])
                y.append(scaled_data[i, 0])

            X, y = np.array(X), np.array(y)
            X = np.reshape(X, (X.shape[0], X.shape[1], 1))

            return X, y, scaler

        except Exception as e:
            self.logger.error("Failed to prepare LSTM data", error=str(e))
            return None, None, None

    def train_lstm_model(
        self,
        prices: pd.Series,
        symbol: str,
        sequence_length: int = 60,
        epochs: int = 50,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """Train LSTM model for price prediction."""
        try:
            # Prepare data
            X, y, scaler = self.prepare_data_for_lstm(prices, sequence_length)

            if X is None:
                return self._fallback_model_training(prices, symbol)

            # Split data
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]

            # Create and train model
            model = self.create_lstm_model(sequence_length)

            if model is None:
                return self._fallback_model_training(prices, symbol)

            # Train model
            history = model.fit(
                X_train, y_train,
                batch_size=batch_size,
                epochs=epochs,
                validation_data=(X_test, y_test),
                verbose=0
            )

            # Make predictions on test set
            predictions = model.predict(X_test, verbose=0)
            predictions = scaler.inverse_transform(predictions)
            y_test_original = scaler.inverse_transform(y_test.reshape(-1, 1))

            # Calculate metrics
            mae = mean_absolute_error(y_test_original, predictions)
            rmse = np.sqrt(mean_squared_error(y_test_original, predictions))
            mape = np.mean(np.abs((y_test_original - predictions) / y_test_original)) * 100

            # Store model and scaler
            self.models[symbol] = model
            self.scalers[symbol] = scaler

            training_result = {
                "model_type": "LSTM",
                "symbol": symbol,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "mae": float(mae),
                "rmse": float(rmse),
                "mape": float(mape),
                "final_loss": float(history.history['loss'][-1]),
                "final_val_loss": float(history.history['val_loss'][-1]),
                "training_completed": datetime.utcnow().isoformat()
            }

            self.logger.info(f"LSTM model trained for {symbol}", metrics=training_result)
            return training_result

        except Exception as e:
            self.logger.error(f"Failed to train LSTM model for {symbol}", error=str(e))
            return self._fallback_model_training(prices, symbol)

    def _fallback_model_training(self, prices: pd.Series, symbol: str) -> Dict[str, Any]:
        """Fallback to simple statistical model if LSTM fails."""
        try:
            if not SKLEARN_AVAILABLE:
                return self._simple_trend_model(prices, symbol)

            # Use Random Forest as fallback
            # Create features (moving averages, RSI-like features)
            df = pd.DataFrame({'price': prices})

            # Technical features
            df['sma_5'] = df['price'].rolling(window=5).mean()
            df['sma_20'] = df['price'].rolling(window=20).mean()
            df['sma_50'] = df['price'].rolling(window=50).mean()
            df['rsi_like'] = self._calculate_rsi_like(df['price'])
            df['price_change'] = df['price'].pct_change()
            df['volatility'] = df['price_change'].rolling(window=20).std()

            # Create target (next day price)
            df['target'] = df['price'].shift(-1)

            # Remove NaN values
            df = df.dropna()

            if len(df) < 100:
                return self._simple_trend_model(prices, symbol)

            # Prepare features
            feature_columns = ['sma_5', 'sma_20', 'sma_50', 'rsi_like', 'price_change', 'volatility']
            X = df[feature_columns].values
            y = df['target'].values

            # Split data
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]

            # Train Random Forest
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            # Make predictions
            predictions = model.predict(X_test)

            # Calculate metrics
            mae = mean_absolute_error(y_test, predictions)
            rmse = np.sqrt(mean_squared_error(y_test, predictions))
            mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100

            # Store model
            self.models[symbol] = {
                'model': model,
                'feature_columns': feature_columns,
                'last_data': df.iloc[-50:].copy()  # Keep last 50 rows for prediction
            }

            training_result = {
                "model_type": "Random Forest",
                "symbol": symbol,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "mae": float(mae),
                "rmse": float(rmse),
                "mape": float(mape),
                "feature_importance": dict(zip(feature_columns, model.feature_importances_)),
                "training_completed": datetime.utcnow().isoformat()
            }

            self.logger.info(f"Random Forest model trained for {symbol}", metrics=training_result)
            return training_result

        except Exception as e:
            self.logger.error(f"Failed to train fallback model for {symbol}", error=str(e))
            return self._simple_trend_model(prices, symbol)

    def _simple_trend_model(self, prices: pd.Series, symbol: str) -> Dict[str, Any]:
        """Simple trend-based model as final fallback."""
        try:
            # Calculate simple trend metrics
            recent_prices = prices.tail(30)
            price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
            volatility = recent_prices.pct_change().std()

            # Store simple model
            self.models[symbol] = {
                'model_type': 'simple_trend',
                'recent_trend': price_change,
                'volatility': volatility,
                'last_price': prices.iloc[-1]
            }

            return {
                "model_type": "Simple Trend",
                "symbol": symbol,
                "recent_trend": float(price_change),
                "volatility": float(volatility),
                "training_completed": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to create simple trend model for {symbol}", error=str(e))
            return {"error": str(e)}

    def _calculate_rsi_like(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI-like indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def predict_prices(
        self,
        symbol: str,
        days_ahead: int = 30,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Generate price predictions for specified number of days."""
        try:
            if symbol not in self.models:
                return {"error": f"No trained model for {symbol}"}

            model_info = self.models[symbol]

            # Generate predictions based on model type
            if isinstance(model_info, dict) and model_info.get('model_type') == 'simple_trend':
                return self._simple_trend_prediction(symbol, days_ahead, model_info)
            elif hasattr(model_info, 'predict'):  # LSTM model
                return self._lstm_prediction(symbol, days_ahead)
            elif isinstance(model_info, dict) and 'model' in model_info:  # Random Forest
                return self._random_forest_prediction(symbol, days_ahead, model_info)
            else:
                return {"error": "Unknown model type"}

        except Exception as e:
            self.logger.error(f"Failed to generate predictions for {symbol}", error=str(e))
            return {"error": str(e)}

    def _simple_trend_prediction(
        self,
        symbol: str,
        days_ahead: int,
        model_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate predictions using simple trend model."""
        try:
            last_price = model_info['last_price']
            trend = model_info['recent_trend']
            volatility = model_info['volatility']

            predictions = []
            dates = pd.date_range(start=datetime.now() + timedelta(days=1), periods=days_ahead, freq='D')

            current_price = last_price

            for i, date in enumerate(dates):
                # Apply trend with some decay
                trend_factor = trend * (0.95 ** i)  # Trend decays over time
                random_factor = np.random.normal(0, volatility)

                predicted_price = current_price * (1 + trend_factor/days_ahead + random_factor/10)

                # Calculate confidence interval
                confidence_range = predicted_price * volatility * 2
                lower_bound = predicted_price - confidence_range
                upper_bound = predicted_price + confidence_range

                predictions.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "predicted_price": round(predicted_price, 2),
                    "confidence_lower": round(lower_bound, 2),
                    "confidence_upper": round(upper_bound, 2),
                    "trend_contribution": round(trend_factor, 4)
                })

                current_price = predicted_price

            return {
                "symbol": symbol,
                "model_type": "Simple Trend",
                "predictions": predictions,
                "model_metrics": {
                    "recent_trend": model_info['recent_trend'],
                    "volatility": model_info['volatility']
                },
                "prediction_date": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed simple trend prediction for {symbol}", error=str(e))
            return {"error": str(e)}

    def _random_forest_prediction(
        self,
        symbol: str,
        days_ahead: int,
        model_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate predictions using Random Forest model."""
        try:
            model = model_info['model']
            feature_columns = model_info['feature_columns']
            last_data = model_info['last_data'].copy()

            predictions = []
            dates = pd.date_range(start=datetime.now() + timedelta(days=1), periods=days_ahead, freq='D')

            for i, date in enumerate(dates):
                # Prepare features from last available data
                latest_features = last_data[feature_columns].iloc[-1].values.reshape(1, -1)

                # Make prediction
                predicted_price = model.predict(latest_features)[0]

                # Estimate confidence interval (simple approach)
                recent_errors = abs(last_data['price'].iloc[-10:] -
                                  model.predict(last_data[feature_columns].iloc[-10:]))
                confidence_range = recent_errors.std() * 2

                lower_bound = predicted_price - confidence_range
                upper_bound = predicted_price + confidence_range

                predictions.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "predicted_price": round(predicted_price, 2),
                    "confidence_lower": round(lower_bound, 2),
                    "confidence_upper": round(upper_bound, 2)
                })

                # Update last_data with prediction for next iteration
                new_row = last_data.iloc[-1].copy()
                new_row['price'] = predicted_price
                new_row.name = len(last_data)

                # Recalculate technical features
                temp_df = pd.concat([last_data['price'], pd.Series([predicted_price])])
                new_row['sma_5'] = temp_df.tail(5).mean()
                new_row['sma_20'] = temp_df.tail(20).mean()
                new_row['sma_50'] = temp_df.tail(50).mean()

                last_data = pd.concat([last_data, new_row.to_frame().T])

            return {
                "symbol": symbol,
                "model_type": "Random Forest",
                "predictions": predictions,
                "model_metrics": model_info.get('training_metrics', {}),
                "prediction_date": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed Random Forest prediction for {symbol}", error=str(e))
            return {"error": str(e)}

    def get_model_performance(self, symbol: str) -> Dict[str, Any]:
        """Get performance metrics for a trained model."""
        try:
            if symbol not in self.models:
                return {"error": f"No model found for {symbol}"}

            model_info = self.models[symbol]

            if isinstance(model_info, dict):
                return {
                    "symbol": symbol,
                    "model_type": model_info.get('model_type', 'Unknown'),
                    "metrics": model_info.get('training_metrics', {}),
                    "last_updated": model_info.get('training_completed', 'Unknown')
                }

            return {
                "symbol": symbol,
                "model_type": "LSTM",
                "status": "Model available",
                "last_updated": "Recently trained"
            }

        except Exception as e:
            self.logger.error(f"Failed to get model performance for {symbol}", error=str(e))
            return {"error": str(e)}

    def generate_forecast_report(
        self,
        symbols: List[str],
        forecast_horizon: int = 30
    ) -> Dict[str, Any]:
        """Generate comprehensive forecast report for multiple symbols."""
        try:
            forecasts = {}
            model_performance = {}

            for symbol in symbols:
                # Get predictions
                predictions = self.predict_prices(symbol, forecast_horizon)
                if "error" not in predictions:
                    forecasts[symbol] = predictions

                # Get model performance
                performance = self.get_model_performance(symbol)
                if "error" not in performance:
                    model_performance[symbol] = performance

            # Generate summary statistics
            summary = {
                "total_symbols": len(symbols),
                "successful_forecasts": len(forecasts),
                "forecast_horizon_days": forecast_horizon,
                "models_used": list(set([perf.get("model_type", "Unknown")
                                       for perf in model_performance.values()])),
                "generated_at": datetime.utcnow().isoformat()
            }

            return {
                "summary": summary,
                "forecasts": forecasts,
                "model_performance": model_performance
            }

        except Exception as e:
            self.logger.error("Failed to generate forecast report", error=str(e))
            return {"error": str(e)}