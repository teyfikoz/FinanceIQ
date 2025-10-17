from sqlalchemy import (
    Column, String, Float, DateTime, Integer, Text, Boolean, JSON, Index
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any

Base = declarative_base()


class MarketData(Base):
    """Table for storing market data (OHLCV)."""
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    source = Column(String(50), nullable=False)  # coingecko, yahoo, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_market_data_symbol_timestamp', 'symbol', 'timestamp'),
    )


class MacroIndicator(Base):
    """Table for storing macroeconomic indicators."""
    __tablename__ = "macro_indicators"

    id = Column(Integer, primary_key=True, index=True)
    indicator_code = Column(String(50), nullable=False, index=True)  # FRED series ID
    indicator_name = Column(String(200), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    frequency = Column(String(20), nullable=True)  # daily, weekly, monthly
    unit = Column(String(50), nullable=True)
    source = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('ix_macro_indicator_code_timestamp', 'indicator_code', 'timestamp'),
    )


class CorrelationMatrix(Base):
    """Table for storing pre-calculated correlation matrices."""
    __tablename__ = "correlation_matrices"

    id = Column(Integer, primary_key=True, index=True)
    window_days = Column(Integer, nullable=False)
    calculation_date = Column(DateTime(timezone=True), nullable=False, index=True)
    asset_1 = Column(String(20), nullable=False)
    asset_2 = Column(String(20), nullable=False)
    correlation = Column(Float, nullable=False)
    p_value = Column(Float, nullable=True)
    observations = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_correlation_date_window', 'calculation_date', 'window_days'),
        Index('ix_correlation_assets', 'asset_1', 'asset_2'),
    )


class LiquidityMetric(Base):
    """Table for storing global liquidity metrics."""
    __tablename__ = "liquidity_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    currency = Column(String(10), nullable=True)  # USD, EUR, JPY
    central_bank = Column(String(50), nullable=True)  # FED, ECB, BOJ
    source = Column(String(50), nullable=False)
    extra_data = Column(JSON, nullable=True)  # Additional context
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_liquidity_metric_timestamp', 'metric_name', 'timestamp'),
    )


class PredictionResult(Base):
    """Table for storing ML model predictions."""
    __tablename__ = "prediction_results"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), nullable=False)
    model_version = Column(String(20), nullable=False)
    asset = Column(String(20), nullable=False, index=True)
    prediction_date = Column(DateTime(timezone=True), nullable=False)
    target_date = Column(DateTime(timezone=True), nullable=False, index=True)
    predicted_value = Column(Float, nullable=False)
    confidence_lower = Column(Float, nullable=True)
    confidence_upper = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)  # Filled after target_date
    error = Column(Float, nullable=True)  # prediction error
    features_used = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_prediction_asset_target', 'asset', 'target_date'),
    )


class RiskMetric(Base):
    """Table for storing risk calculations."""
    __tablename__ = "risk_metrics"

    id = Column(Integer, primary_key=True, index=True)
    asset = Column(String(20), nullable=False, index=True)
    calculation_date = Column(DateTime(timezone=True), nullable=False, index=True)
    window_days = Column(Integer, nullable=False)
    volatility = Column(Float, nullable=True)
    var_95 = Column(Float, nullable=True)  # Value at Risk 95%
    var_99 = Column(Float, nullable=True)  # Value at Risk 99%
    cvar_95 = Column(Float, nullable=True)  # Conditional VaR 95%
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    calmar_ratio = Column(Float, nullable=True)
    skewness = Column(Float, nullable=True)
    kurtosis = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_risk_asset_date', 'asset', 'calculation_date'),
    )


class SentimentData(Base):
    """Table for storing sentiment indicators."""
    __tablename__ = "sentiment_data"

    id = Column(Integer, primary_key=True, index=True)
    indicator_name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    classification = Column(String(50), nullable=True)  # Fear, Greed, Neutral
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(50), nullable=False)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_sentiment_name_timestamp', 'indicator_name', 'timestamp'),
    )


class Alert(Base):
    """Table for storing system alerts."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    asset = Column(String(20), nullable=True)
    threshold_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('ix_alert_type_active', 'alert_type', 'is_active'),
    )


class DataUpdateLog(Base):
    """Table for tracking data update history."""
    __tablename__ = "data_update_logs"

    id = Column(Integer, primary_key=True, index=True)
    data_source = Column(String(50), nullable=False, index=True)
    update_type = Column(String(50), nullable=False)  # full, incremental
    status = Column(String(20), nullable=False)  # success, failed, partial
    records_processed = Column(Integer, nullable=True)
    records_inserted = Column(Integer, nullable=True)
    records_updated = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)  # seconds
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_update_log_source_status', 'data_source', 'status'),
    )


class UserPreference(Base):
    """Table for storing user dashboard preferences."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)  # session or user ID
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('ix_user_pref_user_key', 'user_id', 'preference_key'),
    )


class Fund(Base):
    """Table for storing fund information."""
    __tablename__ = "funds"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    fund_type = Column(String(50), nullable=False)  # ETF, Mutual Fund, etc.
    total_assets = Column(Float, nullable=True)
    expense_ratio = Column(Float, nullable=True)
    inception_date = Column(DateTime(timezone=True), nullable=True)
    category = Column(String(100), nullable=True)  # Sector, International, etc.
    benchmark = Column(String(50), nullable=True)
    data_source = Column(String(50), nullable=False)
    last_updated = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('ix_fund_symbol_type', 'symbol', 'fund_type'),
    )


class FundHolding(Base):
    """Table for storing fund holdings data."""
    __tablename__ = "fund_holdings"

    id = Column(Integer, primary_key=True, index=True)
    fund_symbol = Column(String(20), nullable=False, index=True)
    holding_symbol = Column(String(20), nullable=True)  # May be null for non-stock holdings
    holding_name = Column(String(200), nullable=False)
    holding_type = Column(String(50), nullable=True)  # Stock, Bond, Cash, etc.
    shares = Column(Float, nullable=True)
    market_value = Column(Float, nullable=True)
    weight_percent = Column(Float, nullable=False)  # Percentage of fund
    sector = Column(String(100), nullable=True)
    country = Column(String(50), nullable=True)
    as_of_date = Column(DateTime(timezone=True), nullable=False, index=True)
    data_source = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_fund_holding_fund_date', 'fund_symbol', 'as_of_date'),
        Index('ix_fund_holding_holding_symbol', 'holding_symbol'),
    )


class FundPerformance(Base):
    """Table for storing fund performance metrics."""
    __tablename__ = "fund_performance"

    id = Column(Integer, primary_key=True, index=True)
    fund_symbol = Column(String(20), nullable=False, index=True)
    performance_date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_days = Column(Integer, nullable=False)  # 30, 90, 365, etc.
    total_return = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    alpha = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    tracking_error = Column(Float, nullable=True)
    information_ratio = Column(Float, nullable=True)
    data_source = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_fund_perf_symbol_date', 'fund_symbol', 'performance_date'),
        Index('ix_fund_perf_period', 'period_days'),
    )


class FundSectorAllocation(Base):
    """Table for storing fund sector allocation data."""
    __tablename__ = "fund_sector_allocations"

    id = Column(Integer, primary_key=True, index=True)
    fund_symbol = Column(String(20), nullable=False, index=True)
    sector_name = Column(String(100), nullable=False)
    weight_percent = Column(Float, nullable=False)
    as_of_date = Column(DateTime(timezone=True), nullable=False, index=True)
    data_source = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_fund_sector_fund_date', 'fund_symbol', 'as_of_date'),
        Index('ix_fund_sector_sector', 'sector_name'),
    )


class StockFundRelation(Base):
    """Table for tracking which funds hold which stocks."""
    __tablename__ = "stock_fund_relations"

    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String(20), nullable=False, index=True)
    fund_symbol = Column(String(20), nullable=False, index=True)
    weight_percent = Column(Float, nullable=False)
    shares_held = Column(Float, nullable=True)
    market_value = Column(Float, nullable=True)
    as_of_date = Column(DateTime(timezone=True), nullable=False, index=True)
    data_source = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_stock_fund_stock_date', 'stock_symbol', 'as_of_date'),
        Index('ix_stock_fund_fund_date', 'fund_symbol', 'as_of_date'),
        Index('ix_stock_fund_stock_fund', 'stock_symbol', 'fund_symbol'),
    )