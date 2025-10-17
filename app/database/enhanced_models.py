#!/usr/bin/env python3
"""
Enhanced Database Models for Comprehensive Financial Platform
Supports 10,000+ stocks and 5,000+ funds with institutional-grade analytics
"""

from sqlalchemy import (
    Column, String, Float, DateTime, Integer, Text, Boolean, JSON, Index,
    ForeignKey, DECIMAL, Date, BigInteger, Enum
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any
import enum

Base = declarative_base()

class MarketType(enum.Enum):
    STOCK = "stock"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    BOND = "bond"
    OPTION = "option"
    CRYPTO = "crypto"

class SectorType(enum.Enum):
    TECHNOLOGY = "Technology"
    HEALTHCARE = "Healthcare"
    FINANCIAL = "Financial Services"
    CONSUMER_CYCLICAL = "Consumer Cyclical"
    INDUSTRIALS = "Industrials"
    COMMUNICATION = "Communication Services"
    CONSUMER_DEFENSIVE = "Consumer Defensive"
    ENERGY = "Energy"
    UTILITIES = "Utilities"
    REAL_ESTATE = "Real Estate"
    MATERIALS = "Basic Materials"

# ================ CORE ASSET TABLES ================

class StockMaster(Base):
    """Master table for all stocks (10,000+ global stocks)"""
    __tablename__ = "stocks_master"

    symbol = Column(String(20), primary_key=True)
    company_name = Column(String(300), nullable=False)
    exchange = Column(String(20), nullable=False)  # NYSE, NASDAQ, LSE, etc.
    country = Column(String(50), nullable=False)
    sector = Column(Enum(SectorType), nullable=True)
    industry = Column(String(150), nullable=True)
    market_cap = Column(BigInteger, nullable=True)
    employees = Column(Integer, nullable=True)
    founded_year = Column(Integer, nullable=True)

    # Basic metrics
    current_price = Column(DECIMAL(15,4), nullable=True)
    previous_close = Column(DECIMAL(15,4), nullable=True)
    day_change = Column(DECIMAL(8,4), nullable=True)
    day_change_percent = Column(DECIMAL(8,4), nullable=True)
    volume = Column(BigInteger, nullable=True)
    avg_volume = Column(BigInteger, nullable=True)

    # Valuation metrics
    pe_ratio = Column(DECIMAL(8,2), nullable=True)
    forward_pe = Column(DECIMAL(8,2), nullable=True)
    peg_ratio = Column(DECIMAL(8,2), nullable=True)
    pb_ratio = Column(DECIMAL(8,2), nullable=True)
    ps_ratio = Column(DECIMAL(8,2), nullable=True)
    price_to_cash = Column(DECIMAL(8,2), nullable=True)
    ev_revenue = Column(DECIMAL(8,2), nullable=True)
    ev_ebitda = Column(DECIMAL(8,2), nullable=True)

    # Profitability metrics
    profit_margin = Column(DECIMAL(8,4), nullable=True)
    operating_margin = Column(DECIMAL(8,4), nullable=True)
    return_on_assets = Column(DECIMAL(8,4), nullable=True)
    return_on_equity = Column(DECIMAL(8,4), nullable=True)
    return_on_invested_capital = Column(DECIMAL(8,4), nullable=True)

    # Growth metrics
    revenue_growth = Column(DECIMAL(8,4), nullable=True)
    earnings_growth = Column(DECIMAL(8,4), nullable=True)
    revenue_growth_5y = Column(DECIMAL(8,4), nullable=True)
    earnings_growth_5y = Column(DECIMAL(8,4), nullable=True)

    # Financial strength
    debt_to_equity = Column(DECIMAL(8,4), nullable=True)
    current_ratio = Column(DECIMAL(8,4), nullable=True)
    quick_ratio = Column(DECIMAL(8,4), nullable=True)
    cash_per_share = Column(DECIMAL(8,4), nullable=True)
    book_value_per_share = Column(DECIMAL(8,4), nullable=True)

    # Dividend info
    dividend_yield = Column(DECIMAL(8,4), nullable=True)
    dividend_rate = Column(DECIMAL(8,4), nullable=True)
    payout_ratio = Column(DECIMAL(8,4), nullable=True)
    dividend_growth_5y = Column(DECIMAL(8,4), nullable=True)

    # Risk metrics
    beta = Column(DECIMAL(8,4), nullable=True)
    volatility_52w = Column(DECIMAL(8,4), nullable=True)
    price_52w_high = Column(DECIMAL(15,4), nullable=True)
    price_52w_low = Column(DECIMAL(15,4), nullable=True)

    # Technical indicators
    rsi_14 = Column(DECIMAL(8,4), nullable=True)
    sma_20 = Column(DECIMAL(15,4), nullable=True)
    sma_50 = Column(DECIMAL(15,4), nullable=True)
    sma_200 = Column(DECIMAL(15,4), nullable=True)

    # Timestamps
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_stocks_sector_country', 'sector', 'country'),
        Index('ix_stocks_market_cap', 'market_cap'),
        Index('ix_stocks_pe_ratio', 'pe_ratio'),
        Index('ix_stocks_performance', 'day_change_percent'),
    )

class FundMaster(Base):
    """Master table for all funds (5,000+ funds including ETFs and mutual funds)"""
    __tablename__ = "funds_master"

    symbol = Column(String(20), primary_key=True)
    fund_name = Column(String(300), nullable=False)
    fund_type = Column(Enum(MarketType), nullable=False)  # ETF, MUTUAL_FUND
    fund_family = Column(String(100), nullable=True)  # Vanguard, BlackRock, etc.
    category = Column(String(100), nullable=True)  # Large Growth, International, etc.

    # Basic info
    inception_date = Column(Date, nullable=True)
    total_assets = Column(BigInteger, nullable=True)  # AUM
    shares_outstanding = Column(BigInteger, nullable=True)

    # Pricing
    nav = Column(DECIMAL(15,4), nullable=True)
    previous_nav = Column(DECIMAL(15,4), nullable=True)
    nav_change = Column(DECIMAL(8,4), nullable=True)
    nav_change_percent = Column(DECIMAL(8,4), nullable=True)

    # Costs
    expense_ratio = Column(DECIMAL(6,4), nullable=True)
    management_fee = Column(DECIMAL(6,4), nullable=True)
    front_load = Column(DECIMAL(6,4), nullable=True)
    back_load = Column(DECIMAL(6,4), nullable=True)
    min_investment = Column(Integer, nullable=True)

    # Performance metrics
    return_1d = Column(DECIMAL(8,4), nullable=True)
    return_1w = Column(DECIMAL(8,4), nullable=True)
    return_1m = Column(DECIMAL(8,4), nullable=True)
    return_3m = Column(DECIMAL(8,4), nullable=True)
    return_6m = Column(DECIMAL(8,4), nullable=True)
    return_1y = Column(DECIMAL(8,4), nullable=True)
    return_3y = Column(DECIMAL(8,4), nullable=True)
    return_5y = Column(DECIMAL(8,4), nullable=True)
    return_10y = Column(DECIMAL(8,4), nullable=True)

    # Risk metrics
    volatility_3y = Column(DECIMAL(8,4), nullable=True)
    sharpe_ratio_3y = Column(DECIMAL(8,4), nullable=True)
    sortino_ratio_3y = Column(DECIMAL(8,4), nullable=True)
    max_drawdown_3y = Column(DECIMAL(8,4), nullable=True)
    beta_3y = Column(DECIMAL(8,4), nullable=True)

    # Style metrics
    avg_market_cap = Column(BigInteger, nullable=True)
    median_market_cap = Column(BigInteger, nullable=True)
    price_earnings = Column(DECIMAL(8,4), nullable=True)
    price_book = Column(DECIMAL(8,4), nullable=True)
    price_sales = Column(DECIMAL(8,4), nullable=True)
    price_cash_flow = Column(DECIMAL(8,4), nullable=True)

    # Concentration metrics
    top_10_holdings_percent = Column(DECIMAL(8,4), nullable=True)
    number_of_holdings = Column(Integer, nullable=True)
    turnover_rate = Column(DECIMAL(8,4), nullable=True)

    # Distribution info
    dividend_yield = Column(DECIMAL(8,4), nullable=True)
    distribution_frequency = Column(String(20), nullable=True)
    capital_gains_rate = Column(DECIMAL(8,4), nullable=True)

    # Timestamps
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_funds_type_category', 'fund_type', 'category'),
        Index('ix_funds_expense_ratio', 'expense_ratio'),
        Index('ix_funds_performance', 'return_1y'),
        Index('ix_funds_assets', 'total_assets'),
    )

# ================ FINANCIAL STATEMENTS ================

class FinancialStatements(Base):
    """Comprehensive financial statements data"""
    __tablename__ = "financial_statements"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), ForeignKey('stocks_master.symbol'), nullable=False)
    period_type = Column(String(10), nullable=False)  # 'annual' or 'quarterly'
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer, nullable=True)
    report_date = Column(Date, nullable=False)
    filing_date = Column(Date, nullable=True)

    # Income Statement
    revenue = Column(BigInteger, nullable=True)
    cost_of_revenue = Column(BigInteger, nullable=True)
    gross_profit = Column(BigInteger, nullable=True)
    operating_expenses = Column(BigInteger, nullable=True)
    operating_income = Column(BigInteger, nullable=True)
    ebitda = Column(BigInteger, nullable=True)
    interest_expense = Column(BigInteger, nullable=True)
    pretax_income = Column(BigInteger, nullable=True)
    tax_provision = Column(BigInteger, nullable=True)
    net_income = Column(BigInteger, nullable=True)
    net_income_common = Column(BigInteger, nullable=True)
    eps_basic = Column(DECIMAL(8,4), nullable=True)
    eps_diluted = Column(DECIMAL(8,4), nullable=True)
    shares_basic = Column(BigInteger, nullable=True)
    shares_diluted = Column(BigInteger, nullable=True)

    # Balance Sheet
    total_assets = Column(BigInteger, nullable=True)
    current_assets = Column(BigInteger, nullable=True)
    cash_and_equivalents = Column(BigInteger, nullable=True)
    short_term_investments = Column(BigInteger, nullable=True)
    accounts_receivable = Column(BigInteger, nullable=True)
    inventory = Column(BigInteger, nullable=True)
    other_current_assets = Column(BigInteger, nullable=True)
    ppe_net = Column(BigInteger, nullable=True)
    goodwill = Column(BigInteger, nullable=True)
    intangible_assets = Column(BigInteger, nullable=True)
    other_assets = Column(BigInteger, nullable=True)

    total_liabilities = Column(BigInteger, nullable=True)
    current_liabilities = Column(BigInteger, nullable=True)
    accounts_payable = Column(BigInteger, nullable=True)
    short_term_debt = Column(BigInteger, nullable=True)
    other_current_liabilities = Column(BigInteger, nullable=True)
    long_term_debt = Column(BigInteger, nullable=True)
    other_liabilities = Column(BigInteger, nullable=True)

    total_equity = Column(BigInteger, nullable=True)
    shareholders_equity = Column(BigInteger, nullable=True)
    retained_earnings = Column(BigInteger, nullable=True)

    # Cash Flow Statement
    operating_cash_flow = Column(BigInteger, nullable=True)
    investing_cash_flow = Column(BigInteger, nullable=True)
    financing_cash_flow = Column(BigInteger, nullable=True)
    free_cash_flow = Column(BigInteger, nullable=True)
    capex = Column(BigInteger, nullable=True)
    dividends_paid = Column(BigInteger, nullable=True)
    share_repurchases = Column(BigInteger, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_financials_symbol_period', 'symbol', 'period_type', 'fiscal_year'),
        Index('ix_financials_revenue', 'revenue'),
        Index('ix_financials_net_income', 'net_income'),
    )

# ================ PRICE & MARKET DATA ================

class PriceHistory(Base):
    """Historical price and volume data"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    price_date = Column(Date, nullable=False)
    open_price = Column(DECIMAL(15,4), nullable=False)
    high_price = Column(DECIMAL(15,4), nullable=False)
    low_price = Column(DECIMAL(15,4), nullable=False)
    close_price = Column(DECIMAL(15,4), nullable=False)
    adjusted_close = Column(DECIMAL(15,4), nullable=False)
    volume = Column(BigInteger, nullable=False)

    # Additional metrics
    vwap = Column(DECIMAL(15,4), nullable=True)  # Volume Weighted Average Price
    dollar_volume = Column(BigInteger, nullable=True)
    split_factor = Column(DECIMAL(8,4), nullable=True)
    dividend_amount = Column(DECIMAL(8,4), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_price_symbol_date', 'symbol', 'price_date'),
        Index('ix_price_date', 'price_date'),
        Index('ix_price_volume', 'volume'),
    )

class TechnicalIndicators(Base):
    """Technical analysis indicators"""
    __tablename__ = "technical_indicators"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    calculation_date = Column(Date, nullable=False)

    # Moving Averages
    sma_5 = Column(DECIMAL(15,4), nullable=True)
    sma_10 = Column(DECIMAL(15,4), nullable=True)
    sma_20 = Column(DECIMAL(15,4), nullable=True)
    sma_50 = Column(DECIMAL(15,4), nullable=True)
    sma_100 = Column(DECIMAL(15,4), nullable=True)
    sma_200 = Column(DECIMAL(15,4), nullable=True)
    ema_12 = Column(DECIMAL(15,4), nullable=True)
    ema_26 = Column(DECIMAL(15,4), nullable=True)

    # Momentum Indicators
    rsi_14 = Column(DECIMAL(8,4), nullable=True)
    rsi_21 = Column(DECIMAL(8,4), nullable=True)
    macd = Column(DECIMAL(8,4), nullable=True)
    macd_signal = Column(DECIMAL(8,4), nullable=True)
    macd_histogram = Column(DECIMAL(8,4), nullable=True)
    stochastic_k = Column(DECIMAL(8,4), nullable=True)
    stochastic_d = Column(DECIMAL(8,4), nullable=True)
    williams_r = Column(DECIMAL(8,4), nullable=True)

    # Bollinger Bands
    bb_upper = Column(DECIMAL(15,4), nullable=True)
    bb_middle = Column(DECIMAL(15,4), nullable=True)
    bb_lower = Column(DECIMAL(15,4), nullable=True)
    bb_width = Column(DECIMAL(8,4), nullable=True)
    bb_percent = Column(DECIMAL(8,4), nullable=True)

    # Volume Indicators
    volume_sma_20 = Column(BigInteger, nullable=True)
    volume_ratio = Column(DECIMAL(8,4), nullable=True)
    on_balance_volume = Column(BigInteger, nullable=True)
    accumulation_distribution = Column(BigInteger, nullable=True)

    # Volatility
    atr_14 = Column(DECIMAL(8,4), nullable=True)
    volatility_20d = Column(DECIMAL(8,4), nullable=True)

    # Support/Resistance
    support_level_1 = Column(DECIMAL(15,4), nullable=True)
    support_level_2 = Column(DECIMAL(15,4), nullable=True)
    resistance_level_1 = Column(DECIMAL(15,4), nullable=True)
    resistance_level_2 = Column(DECIMAL(15,4), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_technical_symbol_date', 'symbol', 'calculation_date'),
        Index('ix_technical_rsi', 'rsi_14'),
        Index('ix_technical_macd', 'macd'),
    )

# ================ FUND HOLDINGS & ANALYTICS ================

class FundHoldingsDetailed(Base):
    """Detailed fund holdings with comprehensive data"""
    __tablename__ = "fund_holdings_detailed"

    id = Column(Integer, primary_key=True)
    fund_symbol = Column(String(20), ForeignKey('funds_master.symbol'), nullable=False)
    holding_symbol = Column(String(20), nullable=True)
    holding_name = Column(String(300), nullable=False)
    holding_type = Column(String(50), nullable=True)  # Stock, Bond, Cash, Other

    # Position details
    shares_held = Column(BigInteger, nullable=True)
    market_value = Column(BigInteger, nullable=True)
    weight_percent = Column(DECIMAL(8,4), nullable=False)
    cost_basis = Column(BigInteger, nullable=True)
    unrealized_gain_loss = Column(BigInteger, nullable=True)

    # Security details
    sector = Column(String(100), nullable=True)
    industry = Column(String(150), nullable=True)
    country = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=True)
    market_cap_category = Column(String(20), nullable=True)  # Large, Mid, Small

    # Additional metrics
    beta = Column(DECIMAL(8,4), nullable=True)
    dividend_yield = Column(DECIMAL(8,4), nullable=True)
    pe_ratio = Column(DECIMAL(8,4), nullable=True)
    price_book = Column(DECIMAL(8,4), nullable=True)

    as_of_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_fund_holdings_fund_date', 'fund_symbol', 'as_of_date'),
        Index('ix_fund_holdings_holding', 'holding_symbol'),
        Index('ix_fund_holdings_weight', 'weight_percent'),
        Index('ix_fund_holdings_sector', 'sector'),
    )

class PortfolioAnalytics(Base):
    """Portfolio-level analytics and metrics"""
    __tablename__ = "portfolio_analytics"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(String(50), nullable=False)  # User-defined portfolio ID
    portfolio_name = Column(String(200), nullable=False)

    # Portfolio composition
    total_value = Column(BigInteger, nullable=False)
    cash_position = Column(BigInteger, nullable=True)
    number_of_positions = Column(Integer, nullable=False)

    # Performance metrics
    total_return_1d = Column(DECIMAL(8,4), nullable=True)
    total_return_1w = Column(DECIMAL(8,4), nullable=True)
    total_return_1m = Column(DECIMAL(8,4), nullable=True)
    total_return_3m = Column(DECIMAL(8,4), nullable=True)
    total_return_6m = Column(DECIMAL(8,4), nullable=True)
    total_return_1y = Column(DECIMAL(8,4), nullable=True)
    total_return_3y = Column(DECIMAL(8,4), nullable=True)

    # Risk metrics
    volatility_1y = Column(DECIMAL(8,4), nullable=True)
    sharpe_ratio_1y = Column(DECIMAL(8,4), nullable=True)
    sortino_ratio_1y = Column(DECIMAL(8,4), nullable=True)
    max_drawdown_1y = Column(DECIMAL(8,4), nullable=True)
    var_95_1y = Column(DECIMAL(8,4), nullable=True)
    var_99_1y = Column(DECIMAL(8,4), nullable=True)
    beta = Column(DECIMAL(8,4), nullable=True)

    # Diversification metrics
    effective_holdings = Column(DECIMAL(8,4), nullable=True)
    concentration_ratio = Column(DECIMAL(8,4), nullable=True)
    correlation_avg = Column(DECIMAL(8,4), nullable=True)

    # Sector allocation
    sector_weights = Column(JSON, nullable=True)
    geographic_weights = Column(JSON, nullable=True)
    market_cap_weights = Column(JSON, nullable=True)

    calculation_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_portfolio_id_date', 'portfolio_id', 'calculation_date'),
        Index('ix_portfolio_performance', 'total_return_1y'),
    )

# ================ SCREENING & RESEARCH ================

class ScreeningResults(Base):
    """Store results from custom screens"""
    __tablename__ = "screening_results"

    id = Column(Integer, primary_key=True)
    screen_name = Column(String(100), nullable=False)
    screen_criteria = Column(JSON, nullable=False)
    symbol = Column(String(20), nullable=False)
    rank_score = Column(DECIMAL(8,4), nullable=True)
    screen_date = Column(Date, nullable=False)

    # Key metrics that triggered inclusion
    triggered_criteria = Column(JSON, nullable=True)
    metric_values = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_screening_name_date', 'screen_name', 'screen_date'),
        Index('ix_screening_rank', 'rank_score'),
    )

class AnalystEstimates(Base):
    """Analyst estimates and consensus data"""
    __tablename__ = "analyst_estimates"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), ForeignKey('stocks_master.symbol'), nullable=False)

    # EPS estimates
    eps_current_year = Column(DECIMAL(8,4), nullable=True)
    eps_next_year = Column(DECIMAL(8,4), nullable=True)
    eps_current_quarter = Column(DECIMAL(8,4), nullable=True)
    eps_next_quarter = Column(DECIMAL(8,4), nullable=True)

    # Revenue estimates
    revenue_current_year = Column(BigInteger, nullable=True)
    revenue_next_year = Column(BigInteger, nullable=True)
    revenue_current_quarter = Column(BigInteger, nullable=True)
    revenue_next_quarter = Column(BigInteger, nullable=True)

    # Growth estimates
    eps_growth_current_year = Column(DECIMAL(8,4), nullable=True)
    eps_growth_next_year = Column(DECIMAL(8,4), nullable=True)
    eps_growth_5y = Column(DECIMAL(8,4), nullable=True)
    revenue_growth_current_year = Column(DECIMAL(8,4), nullable=True)
    revenue_growth_next_year = Column(DECIMAL(8,4), nullable=True)

    # Price targets
    price_target_high = Column(DECIMAL(15,4), nullable=True)
    price_target_low = Column(DECIMAL(15,4), nullable=True)
    price_target_mean = Column(DECIMAL(15,4), nullable=True)
    price_target_median = Column(DECIMAL(15,4), nullable=True)

    # Recommendations
    strong_buy_count = Column(Integer, nullable=True)
    buy_count = Column(Integer, nullable=True)
    hold_count = Column(Integer, nullable=True)
    sell_count = Column(Integer, nullable=True)
    strong_sell_count = Column(Integer, nullable=True)
    recommendation_mean = Column(DECIMAL(3,2), nullable=True)  # 1=Strong Buy, 5=Strong Sell

    number_of_analysts = Column(Integer, nullable=True)
    estimate_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_estimates_symbol_date', 'symbol', 'estimate_date'),
        Index('ix_estimates_price_target', 'price_target_mean'),
    )

# ================ ALTERNATIVE DATA ================

class SentimentData(Base):
    """Market sentiment and alternative data"""
    __tablename__ = "sentiment_data_enhanced"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=True)  # Can be market-wide or stock-specific
    sentiment_type = Column(String(50), nullable=False)  # news, social, options, etc.

    # Sentiment scores
    sentiment_score = Column(DECIMAL(6,4), nullable=False)  # -1 to 1 scale
    sentiment_magnitude = Column(DECIMAL(6,4), nullable=True)  # 0 to 1 scale
    confidence_score = Column(DECIMAL(6,4), nullable=True)

    # Source information
    data_source = Column(String(100), nullable=False)
    source_url = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)

    # Content metrics
    mention_count = Column(Integer, nullable=True)
    share_count = Column(Integer, nullable=True)
    like_count = Column(Integer, nullable=True)
    comment_count = Column(Integer, nullable=True)

    # Text analysis
    keywords = Column(JSON, nullable=True)
    topics = Column(JSON, nullable=True)
    entities = Column(JSON, nullable=True)

    sentiment_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_sentiment_symbol_date', 'symbol', 'sentiment_date'),
        Index('ix_sentiment_type_score', 'sentiment_type', 'sentiment_score'),
    )

class InsiderTrading(Base):
    """Insider trading activity"""
    __tablename__ = "insider_trading"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), ForeignKey('stocks_master.symbol'), nullable=False)

    # Transaction details
    transaction_date = Column(Date, nullable=False)
    filing_date = Column(Date, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # Buy, Sell, Option Exercise
    shares_traded = Column(Integer, nullable=False)
    price_per_share = Column(DECIMAL(15,4), nullable=True)
    total_value = Column(BigInteger, nullable=True)

    # Insider details
    insider_name = Column(String(200), nullable=False)
    insider_title = Column(String(100), nullable=True)
    is_director = Column(Boolean, default=False)
    is_officer = Column(Boolean, default=False)
    is_ten_percent_owner = Column(Boolean, default=False)

    # Ownership details
    shares_owned_before = Column(BigInteger, nullable=True)
    shares_owned_after = Column(BigInteger, nullable=True)
    ownership_percent = Column(DECIMAL(8,4), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_insider_symbol_date', 'symbol', 'transaction_date'),
        Index('ix_insider_type_value', 'transaction_type', 'total_value'),
    )

# ================ RELATIONSHIPS ================

# Add relationships
StockMaster.financial_statements = relationship("FinancialStatements", back_populates="stock")
FinancialStatements.stock = relationship("StockMaster", back_populates="financial_statements")

FundMaster.holdings = relationship("FundHoldingsDetailed", back_populates="fund")
FundHoldingsDetailed.fund = relationship("FundMaster", back_populates="holdings")

StockMaster.analyst_estimates = relationship("AnalystEstimates", back_populates="stock")
AnalystEstimates.stock = relationship("StockMaster", back_populates="analyst_estimates")

StockMaster.insider_trades = relationship("InsiderTrading", back_populates="stock")
InsiderTrading.stock = relationship("StockMaster", back_populates="insider_trades")