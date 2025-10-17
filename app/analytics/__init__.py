# Optional imports with graceful fallback
try:
    from .correlations import CorrelationAnalyzer
except ImportError as e:
    print(f"Warning: CorrelationAnalyzer unavailable: {e}")
    CorrelationAnalyzer = None

try:
    from .risk_metrics import RiskCalculator
except ImportError as e:
    print(f"Warning: RiskCalculator unavailable: {e}")
    RiskCalculator = None

try:
    from .volatility import VolatilityAnalyzer
except ImportError as e:
    print(f"Warning: VolatilityAnalyzer unavailable: {e}")
    VolatilityAnalyzer = None

try:
    from .trends import TrendAnalyzer
except ImportError as e:
    print(f"Warning: TrendAnalyzer unavailable: {e}")
    TrendAnalyzer = None

__all__ = [
    "CorrelationAnalyzer",
    "RiskCalculator",
    "VolatilityAnalyzer",
    "TrendAnalyzer"
]
