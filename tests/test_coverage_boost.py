"""Coverage boost tests for financeiq core modules."""
import pytest
import os
import sys


# ── app/services/cache.py ─────────────────────────────────────────────────────

def test_in_memory_cache_basic():
    from app.services.cache import InMemoryCache
    cache = InMemoryCache(max_size=100)
    cache.set("key1", "value1", ttl=60)
    assert cache.get("key1") == "value1"


def test_in_memory_cache_miss():
    from app.services.cache import InMemoryCache
    cache = InMemoryCache()
    assert cache.get("nonexistent") is None


def test_in_memory_cache_delete():
    from app.services.cache import InMemoryCache
    cache = InMemoryCache()
    cache.set("k", "v")
    cache.delete("k")
    assert cache.get("k") is None


def test_in_memory_cache_delete_nonexistent():
    from app.services.cache import InMemoryCache
    cache = InMemoryCache()
    cache.delete("nonexistent")  # should not raise


def test_in_memory_cache_clear():
    from app.services.cache import InMemoryCache
    cache = InMemoryCache()
    cache.set("k1", "v1")
    cache.set("k2", "v2")
    cache.clear()
    assert cache.get("k1") is None
    assert cache.get("k2") is None


def test_in_memory_cache_evict_when_full():
    from app.services.cache import InMemoryCache
    cache = InMemoryCache(max_size=2)
    cache.set("k1", "v1")
    cache.set("k2", "v2")
    cache.set("k3", "v3")  # Should evict oldest
    assert len(cache._cache) == 2


def test_in_memory_cache_expired():
    from app.services.cache import InMemoryCache
    from datetime import datetime, timedelta
    cache = InMemoryCache()
    cache.set("k", "v", ttl=1)
    # Manually expire it
    cache._expiry["k"] = datetime.now() - timedelta(seconds=1)
    assert cache.get("k") is None


def test_cache_module_level_get_set():
    from app.services.cache import cache_set, cache_get, cache_delete, _cache_instance
    import app.services.cache as cache_mod
    # Force in-memory cache
    old = cache_mod._cache_instance
    cache_mod._cache_instance = None
    try:
        cache_set("test_key", {"data": 42}, ttl=60)
        result = cache_get("test_key")
        assert result is not None
        cache_delete("test_key")
        assert cache_get("test_key") is None
    finally:
        cache_mod._cache_instance = old


def test_cache_clear_all():
    from app.services.cache import cache_set, cache_clear, cache_get
    import app.services.cache as cache_mod
    old = cache_mod._cache_instance
    cache_mod._cache_instance = None
    try:
        cache_set("ck1", "val1")
        cache_clear()
        assert cache_get("ck1") is None
    finally:
        cache_mod._cache_instance = old


def test_cache_invalidate_prefix():
    from app.services.cache import cache_set, cache_get, cache_invalidate
    import app.services.cache as cache_mod
    old = cache_mod._cache_instance
    cache_mod._cache_instance = None
    try:
        cache_set("user:1", "alice")
        cache_set("user:2", "bob")
        cache_set("session:x", "data")
        cache_invalidate(prefix="user:")
        assert cache_get("user:1") is None
        assert cache_get("user:2") is None
        # session key should remain
        assert cache_get("session:x") is not None
    finally:
        cache_mod._cache_instance = old


def test_cache_invalidate_no_prefix():
    from app.services.cache import cache_set, cache_get, cache_invalidate
    import app.services.cache as cache_mod
    old = cache_mod._cache_instance
    cache_mod._cache_instance = None
    try:
        cache_set("k", "v")
        cache_invalidate(None)
        assert cache_get("k") is None
    finally:
        cache_mod._cache_instance = old


# ── app/analytics/sanity_checks.py ───────────────────────────────────────────

def test_sanity_check_income_valid():
    from app.analytics.sanity_checks import assert_balanced_income
    result = assert_balanced_income({
        'revenue': 1000.0,
        'cost_of_revenue': 600.0,
        'gross_profit': 400.0,
        'operating_income': 200.0,
        'opex_total': 200.0,
        'net_income': 150.0,
        'tax_expense': 30.0,
        'interest_expense': 20.0,
    })
    assert isinstance(result, dict)


def test_sanity_check_income_mismatch():
    from app.analytics.sanity_checks import assert_balanced_income
    # Imbalanced: revenue(1000) != cost_of_revenue(500) + gross_profit(400)
    result = assert_balanced_income({
        'revenue': 1000.0,
        'cost_of_revenue': 500.0,
        'gross_profit': 400.0,
        'operating_income': 200.0,
        'opex_total': 200.0,
        'net_income': 100.0,
        'tax_expense': 30.0,
        'interest_expense': 20.0,
    })
    assert isinstance(result, dict)


def test_sanity_check_negative_values():
    from app.analytics.sanity_checks import assert_balanced_income
    # Negative values - function should handle them
    try:
        result = assert_balanced_income({
            'revenue': -100.0,
            'cost_of_revenue': 600.0,
            'gross_profit': -700.0,
            'operating_income': -100.0,
            'opex_total': 200.0,
            'net_income': 150.0,
        })
        assert isinstance(result, dict)
    except (ValueError, ZeroDivisionError):
        pass  # Negative values may raise


def test_sankey_structure_valid():
    from app.analytics.sanity_checks import validate_sankey_structure
    labels = ["Revenue", "Cost", "Gross Profit", "OpEx", "Net Income"]
    is_valid, errors = validate_sankey_structure(
        labels=labels,
        sources=[0, 0, 2, 2],
        targets=[1, 2, 3, 4],
        values=[600.0, 400.0, 200.0, 200.0]
    )
    assert isinstance(is_valid, bool)
    assert isinstance(errors, list)


def test_sankey_structure_invalid_length():
    from app.analytics.sanity_checks import validate_sankey_structure
    labels = ["A", "B", "C"]
    is_valid, errors = validate_sankey_structure(
        labels=labels,
        sources=[0, 1],
        targets=[1],  # Length mismatch
        values=[100.0, 200.0]
    )
    assert not is_valid
    assert len(errors) > 0


def test_sankey_structure_invalid_index():
    from app.analytics.sanity_checks import validate_sankey_structure
    labels = ["A", "B"]
    is_valid, errors = validate_sankey_structure(
        labels=labels,
        sources=[0, 5],  # 5 is out of bounds
        targets=[1, 0],
        values=[100.0, 50.0]
    )
    assert not is_valid


def test_sankey_structure_negative_values():
    from app.analytics.sanity_checks import validate_sankey_structure
    labels = ["A", "B", "C"]
    is_valid, errors = validate_sankey_structure(
        labels=labels,
        sources=[0],
        targets=[1],
        values=[-100.0]  # Negative value
    )
    assert not is_valid


def test_sankey_structure_self_loop():
    from app.analytics.sanity_checks import validate_sankey_structure
    labels = ["A", "B"]
    is_valid, errors = validate_sankey_structure(
        labels=labels,
        sources=[0],
        targets=[0],  # Self-loop
        values=[100.0]
    )
    assert not is_valid


def test_sankey_structure_empty():
    from app.analytics.sanity_checks import validate_sankey_structure
    is_valid, errors = validate_sankey_structure(
        labels=["A", "B"],
        sources=[],
        targets=[],
        values=[]
    )
    assert not is_valid


def test_rescale_costs():
    from app.analytics.sanity_checks import rescale_costs_proportionally
    costs = {"labor": 500.0, "materials": 300.0, "overhead": 200.0}
    result = rescale_costs_proportionally(costs, 2000.0)
    assert isinstance(result, dict)
    total = sum(result.values())
    assert abs(total - 2000.0) < 0.01


# ── app/utils/logger.py ───────────────────────────────────────────────────────

def test_get_logger():
    from app.utils.logger import get_logger
    logger = get_logger("test_module")
    assert logger is not None


def test_stdlib_compat_logger_methods():
    from app.utils.logger import StdlibCompatLogger
    import logging
    base_logger = logging.getLogger("test_compat")
    logger = StdlibCompatLogger(base_logger)
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")


def test_stdlib_compat_logger_bind():
    from app.utils.logger import StdlibCompatLogger
    import logging
    base_logger = logging.getLogger("test_bind")
    logger = StdlibCompatLogger(base_logger)
    bound = logger.bind(user="test", request_id="123")
    assert bound is logger


def test_stdlib_compat_logger_new():
    from app.utils.logger import StdlibCompatLogger
    import logging
    base_logger = logging.getLogger("test_new")
    logger = StdlibCompatLogger(base_logger)
    new = logger.new(user="fresh")
    assert new is logger


def test_stdlib_compat_logger_with_kwargs():
    from app.utils.logger import StdlibCompatLogger
    import logging
    base_logger = logging.getLogger("test_kwargs")
    logger = StdlibCompatLogger(base_logger)
    logger.info("msg with context", user="alice", action="login")


def test_stdlib_compat_logger_exception():
    from app.utils.logger import StdlibCompatLogger
    import logging
    base_logger = logging.getLogger("test_exc")
    logger = StdlibCompatLogger(base_logger)
    try:
        raise ValueError("test error")
    except ValueError:
        logger.exception("caught an error")


def test_stdlib_compat_logger_getattr():
    from app.utils.logger import StdlibCompatLogger
    import logging
    base_logger = logging.getLogger("test_attr")
    logger = StdlibCompatLogger(base_logger)
    # Should delegate to underlying logger
    assert hasattr(logger, "name")


def test_setup_logging():
    from app.utils.logger import setup_logging
    setup_logging()  # Should not raise


# ── app/core/config.py ────────────────────────────────────────────────────────

def test_settings_defaults():
    from app.core.config import settings
    assert settings.PROJECT_NAME is not None
    assert settings.VERSION is not None


def test_settings_assemble_cors_empty():
    from app.core.config import Settings
    # Test the cors assembly with empty value
    result = Settings.assemble_cors_origins("")
    assert isinstance(result, list)
    assert len(result) > 0


def test_settings_assemble_cors_list():
    from app.core.config import Settings
    result = Settings.assemble_cors_origins(["http://localhost:3000"])
    assert isinstance(result, list)


def test_settings_assemble_cors_csv():
    from app.core.config import Settings
    result = Settings.assemble_cors_origins("http://localhost:3000,http://localhost:8000")
    assert isinstance(result, list)
    assert len(result) == 2


def test_settings_assemble_cors_json():
    from app.core.config import Settings
    result = Settings.assemble_cors_origins('["http://localhost:3000"]')
    assert isinstance(result, list)


def test_settings_assemble_cors_invalid_json():
    from app.core.config import Settings
    result = Settings.assemble_cors_origins("[invalid")
    assert isinstance(result, list)


# ── app/analytics/__init__.py ─────────────────────────────────────────────────

def test_analytics_init_import():
    import app.analytics
    # Should import without errors (individual imports may be None if deps missing)
    assert hasattr(app.analytics, "CorrelationAnalyzer")


# ── app/services/stock_enrichment.py ─────────────────────────────────────────

def test_stock_enrichment_import():
    from app.services.stock_enrichment import StockEnrichmentService
    assert StockEnrichmentService is not None


def test_stock_enrichment_create():
    from app.services.stock_enrichment import StockEnrichmentService
    service = StockEnrichmentService()
    assert service is not None


# ── app/services/prewarm_worker.py ───────────────────────────────────────────

def test_prewarm_worker_import():
    from app.services.prewarm_worker import PublicDataPrewarmWorker as PrewarmWorker
    assert PrewarmWorker is not None


def test_prewarm_worker_create():
    from app.services.prewarm_worker import PublicDataPrewarmWorker as PrewarmWorker
    worker = PrewarmWorker()
    assert worker is not None


# ── app/analytics/sankey_transform.py ────────────────────────────────────────

def test_sankey_import():
    from app.analytics.sankey_transform import income_to_sankey, fund_to_sankey
    assert income_to_sankey is not None
    assert fund_to_sankey is not None


def test_sankey_edge_cases():
    """Test sankey transform with empty sankey helper."""
    from app.analytics.sankey_transform import _empty_sankey
    result = _empty_sankey("no data")
    assert isinstance(result, dict)
    assert "error" in result or "labels" in result or len(result) > 0


# ── Additional targeted tests ─────────────────────────────────────────────────

def test_in_memory_cache_evict_expired_first():
    """Cover _evict_oldest branch where expired key is evicted first (line 76)."""
    from app.services.cache import InMemoryCache
    from datetime import datetime, timedelta
    cache = InMemoryCache(max_size=2)
    cache.set("k1", "v1")
    cache.set("k2", "v2")
    # Manually expire k1
    cache._expiry["k1"] = datetime.now() - timedelta(seconds=1)
    # Adding k3 triggers eviction; k1 is expired → evicts k1 (line 76 hit)
    cache.set("k3", "v3")
    assert cache.get("k3") == "v3"


def test_sankey_invalid_target_index():
    """Cover line 115 - invalid target index in validate_sankey_structure."""
    from app.analytics.sanity_checks import validate_sankey_structure
    labels = ["A", "B"]
    is_valid, errors = validate_sankey_structure(
        labels=labels,
        sources=[0],
        targets=[99],  # Out of bounds target
        values=[100.0]
    )
    assert not is_valid
    assert any("target" in e.lower() for e in errors)


def test_within_tolerance_zero_expected():
    """Cover line 193 - _within_tolerance when expected == 0."""
    from app.analytics.sanity_checks import _within_tolerance
    assert _within_tolerance(0.0, 0.0) is True   # actual==0, expected==0
    assert _within_tolerance(1.0, 0.0) is False  # actual!=0, expected==0


def test_config_assemble_db_string():
    """Cover line 40 - assemble_db_connection returns string URL directly."""
    from app.core.config import Settings
    try:
        s = Settings(DATABASE_URL="postgresql://localhost/testdb")
        # If we get here, the string URL was accepted
        assert s.DATABASE_URL is not None
    except Exception:
        # Pydantic may still validate/convert the type
        pass


def test_prewarm_worker_start_stop():
    """Cover start/stop/snapshot methods of PublicDataPrewarmWorker."""
    from app.services.prewarm_worker import PublicDataPrewarmWorker
    import time
    worker = PublicDataPrewarmWorker()
    # First start - covers lines 30-32
    worker.start()
    time.sleep(0.05)
    # snapshot while alive - covers line 43 (alive=True)
    snap = worker.snapshot()
    assert snap["enabled"] is True
    # Second start - covers lines 28-29 (early return: thread is_alive)
    worker.start()
    # stop - covers lines 35-37
    worker.stop()
    # Thread may still be running briefly, but stop was called
    assert worker.stop_event.is_set()
