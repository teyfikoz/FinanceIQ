"""
Test yfinance fallback chain functionality.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from app.utils.yfinance_fallback import safe_yf_download, FUTURES_PROXIES


@patch('yfinance.download')
def test_successful_first_attempt(mock_download):
    """Test successful data fetch on first attempt."""
    # Mock successful download
    expected_df = pd.DataFrame({'Close': [100, 101, 102]})
    mock_download.return_value = expected_df

    df, warning = safe_yf_download("AAPL", period="1d", interval="1m")

    assert not df.empty
    assert warning is None
    assert len(df) == 3
    mock_download.assert_called_once_with("AAPL", period="1d", interval="1m", progress=False)


@patch('yfinance.download')
def test_fallback_to_5day(mock_download):
    """Test fallback to 5-day period when 1-day intraday fails."""
    # First call returns empty, second call succeeds
    empty_df = pd.DataFrame()
    success_df = pd.DataFrame({'Close': [100, 101, 102, 103, 104]})

    mock_download.side_effect = [empty_df, success_df]

    df, warning = safe_yf_download("AAPL", period="1d", interval="1m")

    assert not df.empty
    assert warning is not None
    assert "5-day data" in warning
    assert len(df) == 5

    # Verify both calls were made
    assert mock_download.call_count == 2
    calls = mock_download.call_args_list
    assert calls[0][1] == {'period': '1d', 'interval': '1m', 'progress': False}
    assert calls[1][1] == {'period': '5d', 'interval': '1d', 'progress': False}


@patch('yfinance.download')
def test_fallback_to_1month(mock_download):
    """Test fallback to 1-month period when shorter periods fail."""
    # First two calls return empty, third succeeds
    empty_df = pd.DataFrame()
    success_df = pd.DataFrame({'Close': [i for i in range(20)]})

    mock_download.side_effect = [empty_df, empty_df, success_df]

    df, warning = safe_yf_download("AAPL", period="1d", interval="1m")

    assert not df.empty
    assert warning is not None
    assert "1-month data" in warning
    assert len(df) == 20

    # Verify all three calls were made
    assert mock_download.call_count == 3


@patch('yfinance.download')
def test_futures_proxy_fallback(mock_download):
    """Test proxy symbol usage for futures."""
    # First three calls return empty, fourth (proxy) succeeds
    empty_df = pd.DataFrame()
    success_df = pd.DataFrame({'Close': [1800, 1805, 1810]})

    mock_download.side_effect = [empty_df, empty_df, empty_df, success_df]

    # Use gold futures which has proxy mapping
    df, warning = safe_yf_download("GC=F", period="1d", interval="1m")

    assert not df.empty
    assert warning is not None
    assert "proxy" in warning.lower()
    assert "XAUUSD=X" in warning  # Expected proxy

    # Verify proxy was attempted (should be 4th call)
    calls = mock_download.call_args_list
    assert len(calls) == 4
    proxy_call = calls[-1]
    assert proxy_call[0][0] == "XAUUSD=X"


@patch('yfinance.download')
def test_all_attempts_fail(mock_download):
    """Test behavior when all fallback attempts fail."""
    # All calls return empty DataFrame
    mock_download.return_value = pd.DataFrame()

    df, warning = safe_yf_download("INVALID", period="1d", interval="1m")

    assert df.empty
    assert warning is not None
    assert "No data available" in warning


@patch('yfinance.download')
def test_exception_handling(mock_download):
    """Test graceful handling of yfinance exceptions."""
    # First call raises exception, second succeeds
    mock_download.side_effect = [
        Exception("Network error"),
        pd.DataFrame({'Close': [100, 101, 102]})
    ]

    df, warning = safe_yf_download("AAPL", period="1d", interval="1m")

    # Should fall back to 5-day attempt
    assert not df.empty
    assert warning is not None


@patch('yfinance.download')
def test_non_intraday_fallback_chain(mock_download):
    """Test fallback chain for non-intraday requests."""
    # First call empty, skip 5-day fallback (only for intraday), go to 1mo
    empty_df = pd.DataFrame()
    success_df = pd.DataFrame({'Close': [i for i in range(20)]})

    mock_download.side_effect = [empty_df, success_df]

    # Request daily data (not intraday)
    df, warning = safe_yf_download("AAPL", period="5d", interval="1d")

    assert not df.empty
    assert warning is not None
    assert "1-month data" in warning

    # Should skip the "5-day fallback" since original wasn't intraday
    assert mock_download.call_count == 2


def test_futures_proxy_mapping():
    """Test that futures proxy mappings are correctly defined."""
    assert "GC=F" in FUTURES_PROXIES
    assert FUTURES_PROXIES["GC=F"] == "XAUUSD=X"

    assert "SI=F" in FUTURES_PROXIES
    assert FUTURES_PROXIES["SI=F"] == "XAGUSD=X"

    assert "CL=F" in FUTURES_PROXIES
    assert FUTURES_PROXIES["CL=F"] == "BZ=F"


@patch('yfinance.download')
def test_warning_messages_format(mock_download):
    """Test that warning messages are user-friendly and properly formatted."""
    empty_df = pd.DataFrame()
    success_df = pd.DataFrame({'Close': [100]})

    # Test 5-day fallback message
    mock_download.side_effect = [empty_df, success_df]
    _, warning = safe_yf_download("AAPL", period="1d", interval="1m")
    assert warning.startswith("ℹ️")

    # Test 1-month fallback message
    mock_download.side_effect = [empty_df, empty_df, success_df]
    _, warning = safe_yf_download("AAPL", period="1d", interval="1m")
    assert warning.startswith("ℹ️")

    # Test failure message
    mock_download.return_value = empty_df
    _, warning = safe_yf_download("INVALID", period="1d", interval="1m")
    assert warning.startswith("⚠️")
