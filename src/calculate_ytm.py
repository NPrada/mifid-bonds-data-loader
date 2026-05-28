#!/usr/bin/env python3
"""
YTM (Yield to Maturity) calculator for fixed-rate and zero-coupon bonds.

Key assumptions:
- Prices are clean prices expressed as % of par (e.g. 98.5 means 98.5% of face value).
  Yahoo Finance sometimes returns dirty prices; the resulting YTM will carry a small error
  near coupon dates. Treat outputs as indicative, not exact.
- Coupon frequency defaults to annual (most EUR bonds: Bunds, OATs, BTPs).
  Override with coupon_freq=2 for semi-annual (USD/GBP bonds).
- Day count uses actual/365.25 (simplified). A full implementation would use the
  bond's actual day-count convention (Act/Act ICMA for most EUR govts, 30/360 etc.).
"""

from datetime import date

from scipy.optimize import brentq


def calculate_ytm_fixed(
    price_pct: float,
    coupon_rate_pct: float,
    maturity_date_str: str,
    coupon_freq: int = 1,
    settlement_date: date | None = None,
) -> float | None:
    """
    Solve for annualized YTM of a fixed-coupon bond.

    Args:
        price_pct:        Clean price as % of par (e.g. 98.5).
        coupon_rate_pct:  Annual coupon rate as % (e.g. 2.5 means 2.5%).
        maturity_date_str: ISO date string "YYYY-MM-DD".
        coupon_freq:      Coupons per year — 1 (annual) or 2 (semi-annual).
        settlement_date:  Defaults to today.

    Returns:
        Annualized YTM as a decimal (e.g. 0.025 = 2.5%), or None if not solvable.
    """
    if settlement_date is None:
        settlement_date = date.today()

    try:
        maturity = date.fromisoformat(maturity_date_str)
    except (ValueError, TypeError):
        return None

    years = (maturity - settlement_date).days / 365.25
    if years <= 0:
        return None

    n_periods = max(1, round(years * coupon_freq))
    c = coupon_rate_pct / 100 / coupon_freq   # coupon per period as fraction of par
    price = price_pct / 100                    # as fraction of par

    def pv(r: float) -> float:
        if abs(r) < 1e-12:
            return c * n_periods + 1.0
        return c * (1 - (1 + r) ** -n_periods) / r + (1 + r) ** -n_periods

    def objective(r: float) -> float:
        return pv(r) - price

    try:
        r_periodic = brentq(objective, -0.9999, 50.0, xtol=1e-10)
        return r_periodic * coupon_freq
    except (ValueError, RuntimeError):
        return None


def calculate_ytm_zero_coupon(
    price_pct: float,
    maturity_date_str: str,
    settlement_date: date | None = None,
) -> float | None:
    """
    Analytical YTM for a zero-coupon bond: ytm = (par/price)^(1/T) - 1.

    Args:
        price_pct:        Price as % of par (e.g. 85.0).
        maturity_date_str: ISO date string.
        settlement_date:  Defaults to today.

    Returns:
        Annualized YTM as a decimal, or None if not calculable.
    """
    if settlement_date is None:
        settlement_date = date.today()

    try:
        maturity = date.fromisoformat(maturity_date_str)
    except (ValueError, TypeError):
        return None

    years = (maturity - settlement_date).days / 365.25
    if years <= 0:
        return None

    price = price_pct / 100
    if price <= 0:
        return None

    try:
        return (1.0 / price) ** (1.0 / years) - 1.0
    except (ValueError, ZeroDivisionError):
        return None
