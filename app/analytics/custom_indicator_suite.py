#!/usr/bin/env python3
"""Custom multi-timeframe indicator suite with IMSE-safe implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

import numpy as np
import pandas as pd


@dataclass
class ProfileConfig:
    name: str
    period: str
    interval: str
    ema_fast: int
    ema_slow: int
    sma_long: int
    rsi_len: int
    atr_len: int
    adx_len: int
    bb_len: int
    bb_std: float
    imse: Dict[str, Any]


PROFILES: Dict[str, ProfileConfig] = {
    "Günlük": ProfileConfig(
        name="Günlük",
        period="6mo",
        interval="1d",
        ema_fast=9,
        ema_slow=21,
        sma_long=50,
        rsi_len=14,
        atr_len=14,
        adx_len=14,
        bb_len=20,
        bb_std=2.0,
        imse={
            "k_s": 8,
            "w_s": 20,
            "s_s": 0.8,
            "k_m": 21,
            "w_m": 60,
            "s_m": 1.0,
            "k_l": 40,
            "w_l": 120,
            "s_l": 1.0,
            "wgt_s": 0.35,
            "wgt_m": 0.45,
            "wgt_l": 0.20,
            "base_th": 0.14,
            "min_conf": 0.38,
            "atrp_high": 2.0,
            "adx_len": 14,
            "trend_len": 20,
            "trend_scale": 0.5,
            "slope_len": 6,
        },
    ),
    "Kısa Vade": ProfileConfig(
        name="Kısa Vade",
        period="3mo",
        interval="1d",
        ema_fast=8,
        ema_slow=21,
        sma_long=34,
        rsi_len=9,
        atr_len=14,
        adx_len=14,
        bb_len=20,
        bb_std=2.0,
        imse={
            "k_s": 10,
            "w_s": 30,
            "s_s": 1.0,
            "k_m": 20,
            "w_m": 60,
            "s_m": 1.1,
            "k_l": 45,
            "w_l": 120,
            "s_l": 1.1,
            "wgt_s": 0.45,
            "wgt_m": 0.40,
            "wgt_l": 0.15,
            "base_th": 0.16,
            "min_conf": 0.40,
            "atrp_high": 2.2,
            "adx_len": 14,
            "trend_len": 18,
            "trend_scale": 0.6,
            "slope_len": 5,
        },
    ),
    "Orta Vade": ProfileConfig(
        name="Orta Vade",
        period="1y",
        interval="1d",
        ema_fast=12,
        ema_slow=26,
        sma_long=100,
        rsi_len=14,
        atr_len=14,
        adx_len=14,
        bb_len=20,
        bb_std=2.0,
        imse={
            "k_s": 10,
            "w_s": 30,
            "s_s": 1.0,
            "k_m": 25,
            "w_m": 90,
            "s_m": 1.0,
            "k_l": 60,
            "w_l": 180,
            "s_l": 1.0,
            "wgt_s": 0.30,
            "wgt_m": 0.50,
            "wgt_l": 0.20,
            "base_th": 0.15,
            "min_conf": 0.40,
            "atrp_high": 2.0,
            "adx_len": 14,
            "trend_len": 20,
            "trend_scale": 0.5,
            "slope_len": 6,
        },
    ),
    "Uzun Vade": ProfileConfig(
        name="Uzun Vade",
        period="3y",
        interval="1d",
        ema_fast=21,
        ema_slow=55,
        sma_long=200,
        rsi_len=14,
        atr_len=14,
        adx_len=20,
        bb_len=20,
        bb_std=2.0,
        imse={
            "k_s": 12,
            "w_s": 40,
            "s_s": 1.0,
            "k_m": 30,
            "w_m": 120,
            "s_m": 1.0,
            "k_l": 80,
            "w_l": 240,
            "s_l": 1.0,
            "wgt_s": 0.25,
            "wgt_m": 0.50,
            "wgt_l": 0.25,
            "base_th": 0.13,
            "min_conf": 0.38,
            "atrp_high": 1.8,
            "adx_len": 20,
            "trend_len": 30,
            "trend_scale": 0.5,
            "slope_len": 8,
        },
    ),
}


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _calc_adx_safe(df: pd.DataFrame, length: int) -> pd.Series:
    high = df['High']
    low = df['Low']
    close = df['Close']

    up = high.diff()
    down = -low.diff()

    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1 / length, adjust=False).mean()
    atr_safe = atr.replace(0, 1e-9)

    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / length, adjust=False).mean() / atr_safe
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / length, adjust=False).mean() / atr_safe

    denom = (plus_di + minus_di).replace(0, 1e-9)
    dx = 100 * (plus_di - minus_di).abs() / denom
    adx = dx.ewm(alpha=1 / length, adjust=False).mean()

    return adx


def _calc_atr(df: pd.DataFrame, length: int) -> pd.Series:
    high = df['High']
    low = df['Low']
    close = df['Close']

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)

    return tr.ewm(alpha=1 / length, adjust=False).mean()


def _calc_rsi(series: pd.Series, length: int) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(length).mean()
    loss = -delta.where(delta < 0, 0).rolling(length).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def _knn_score(features: np.ndarray, chg: np.ndarray, k_in: int, win_in: int, sens: float) -> np.ndarray:
    n = len(chg)
    scores = np.zeros(n)
    k_eff = max(1, min(k_in, win_in))
    start = min(n, max(win_in + 50, k_eff + 2))

    for t in range(start, n):
        score = 0.0
        wsum = 0.0
        for i in range(1, k_eff + 1):
            if t - i < 0:
                break
            d = np.log1p(np.abs(features[t] - features[t - i])).sum()
            y = 1.0 if chg[t - i] > 0 else -1.0
            w = 1.0 / (1.0 + d * sens)
            score += y * w
            wsum += w
        scores[t] = score / wsum if wsum > 0 else 0.0

    return scores


def compute_imse(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    src = df['Close'].astype(float)
    chg = src.diff().fillna(0.0).to_numpy()

    rsi = _calc_rsi(src, 14) / 100.0
    atr = _calc_atr(df, 14)
    atrp = (atr / src.replace(0, np.nan)).fillna(0.0) * 100.0
    adx = _calc_adx_safe(df, 14) / 100.0
    trend = (src - _ema(src, 50)) / src.replace(0, np.nan)
    trend = trend.replace([np.inf, -np.inf], 0.0).fillna(0.0)

    features = np.vstack([
        rsi.to_numpy(),
        atrp.fillna(0.0).to_numpy(),
        adx.fillna(0.0).to_numpy(),
        trend.to_numpy(),
    ]).T

    s_sco = _knn_score(features, chg, params["k_s"], params["w_s"], params["s_s"])
    m_sco = _knn_score(features, chg, params["k_m"], params["w_m"], params["s_m"])
    l_sco = _knn_score(features, chg, params["k_l"], params["w_l"], params["s_l"])

    w_sum = max(1e-9, params["wgt_s"] + params["wgt_m"] + params["wgt_l"])
    final_score = (params["wgt_s"] * s_sco + params["wgt_m"] * m_sco + params["wgt_l"] * l_sco) / w_sum
    confidence = np.abs(final_score)

    adx_len = params.get("adx_len", 14)
    adx_raw = _calc_adx_safe(df, adx_len).fillna(0.0)
    atrp_raw = (atr / src.replace(0, np.nan)).fillna(0.0) * 100.0

    regime = np.where(atrp_raw > params["atrp_high"], "HIGH_VOL", np.where(adx_raw > 20, "TREND", "RANGE"))
    th_eff = np.where(regime == "RANGE", params["base_th"] * 1.5, np.where(regime == "HIGH_VOL", params["base_th"] * 1.2, params["base_th"]))

    bull = (final_score > th_eff) & (confidence >= params["min_conf"])
    bear = (final_score < -th_eff) & (confidence >= params["min_conf"])

    trend_base = _ema(src, params["trend_len"]) + final_score * _calc_atr(df, 14) * params["trend_scale"]
    trend_slope_raw = trend_base - trend_base.shift(params["slope_len"])
    trend_slope = trend_slope_raw.fillna(0.0)

    return pd.DataFrame({
        "final_score": final_score,
        "confidence": confidence,
        "threshold": th_eff,
        "trend_slope": trend_slope,
        "bull": bull,
        "bear": bear,
        "regime": regime,
        "adx": adx_raw,
        "atrp": atrp_raw,
    }, index=df.index)


def compute_indicator_bundle(df: pd.DataFrame, profile: ProfileConfig) -> Dict[str, Any]:
    if df.empty:
        return {"error": "No data"}

    data = df.copy().dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if data.empty:
        return {"error": "No data"}

    close = data['Close']

    ema_fast = _ema(close, profile.ema_fast)
    ema_slow = _ema(close, profile.ema_slow)
    sma_long = close.rolling(profile.sma_long).mean()

    rsi = _calc_rsi(close, profile.rsi_len)
    atr = _calc_atr(data, profile.atr_len)

    # MACD
    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    macd = ema12 - ema26
    macd_signal = _ema(macd, 9)
    macd_hist = macd - macd_signal

    # Bollinger
    bb_mid = close.rolling(profile.bb_len).mean()
    bb_std = close.rolling(profile.bb_len).std()
    bb_upper = bb_mid + bb_std * profile.bb_std
    bb_lower = bb_mid - bb_std * profile.bb_std

    # IMSE core
    imse = compute_imse(data, profile.imse)

    latest = data.iloc[-1]
    imse_latest = imse.iloc[-1]

    trend_state = "BULL" if imse_latest["bull"] else "BEAR" if imse_latest["bear"] else "NEUTRAL"
    momentum_state = "OVERBOUGHT" if rsi.iloc[-1] > 70 else "OVERSOLD" if rsi.iloc[-1] < 30 else "NEUTRAL"

    return {
        "profile": profile.name,
        "latest": {
            "price": float(latest['Close']),
            "ema_fast": float(ema_fast.iloc[-1]),
            "ema_slow": float(ema_slow.iloc[-1]),
            "sma_long": float(sma_long.iloc[-1]) if not pd.isna(sma_long.iloc[-1]) else None,
            "rsi": float(rsi.iloc[-1]),
            "atr": float(atr.iloc[-1]),
            "macd": float(macd.iloc[-1]),
            "macd_signal": float(macd_signal.iloc[-1]),
            "macd_hist": float(macd_hist.iloc[-1]),
            "trend_state": trend_state,
            "momentum_state": momentum_state,
        },
        "series": {
            "close": close,
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
            "sma_long": sma_long,
            "bb_upper": bb_upper,
            "bb_mid": bb_mid,
            "bb_lower": bb_lower,
        },
        "imse": imse,
    }
