#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "QuantLib",
# ]
# ///

"""
Bond Yield to Maturity (YTM) calculation.

Exposes a single pure function, `calculate_ytm`, that wraps QuantLib
(industry-standard fixed-income library, ~6.8k GitHub stars). QuantLib is
used because it properly supports bond day count conventions, which are
essential for accurate YTM (numpy-financial does not support them).

Intended usage: when scraping a price for a bond, call `calculate_ytm`
with the bond's coupon details and the scraped price, then write the
price + ytm to the database in a single insert.

Only applicable to fixed-rate bonds. Floating-rate and zero-coupon bonds
should be filtered out by the caller before invoking this function.
"""

from datetime import date

import QuantLib as ql

# ---------------------------------------------------------------------------
# Day count conventions: string name -> QuantLib day counter
#
# ActualActual.ISMA is the ICMA standard for European bonds and is the
# default for ESMA FIRDS data. Override via the `day_count` parameter.
# ---------------------------------------------------------------------------

DAY_COUNTERS: dict[str, ql.DayCounter] = {
    "ActualActual.ISMA":   ql.ActualActual(ql.ActualActual.ISMA),
    "ActualActual.Bond":   ql.ActualActual(ql.ActualActual.Bond),
    "ActualActual.ISDA":   ql.ActualActual(ql.ActualActual.ISDA),
    "Thirty360.BondBasis": ql.Thirty360(ql.Thirty360.BondBasis),
    "Thirty360.European":  ql.Thirty360(ql.Thirty360.European),
    "Actual360":           ql.Actual360(),
    "Actual365Fixed":      ql.Actual365Fixed(),
}

FREQUENCIES: dict[str, int] = {
    "Annual":     ql.Annual,
    "Semiannual": ql.Semiannual,
    "Quarterly":  ql.Quarterly,
    "Monthly":    ql.Monthly,
}

DEFAULT_DAY_COUNT = "ActualActual.ISMA"
DEFAULT_FREQUENCY = "Annual"


def _to_ql_date(d: date) -> ql.Date:
    return ql.Date(d.day, d.month, d.year)


def calculate_ytm(
    fixed_rate: float,
    nominal_value: float,
    clean_price_pct: float,
    maturity_date: date,
    settlement_date: date,
    frequency: str = DEFAULT_FREQUENCY,
    day_count: str = DEFAULT_DAY_COUNT,
) -> float | None:
    """
    Calculate Yield to Maturity (YTM) for a fixed-rate bond.

    Args:
        fixed_rate: Annual coupon rate as a percentage (e.g. 2.5 means 2.5%).
        nominal_value: Face/par value per unit (e.g. 1000).
        clean_price_pct: Clean price as a percentage of par (e.g. 98.5).
        maturity_date: Bond maturity date.
        settlement_date: Date the price applies to (used as settlement).
        frequency: Coupon frequency name. See FREQUENCIES dict.
        day_count: Day count convention name. See DAY_COUNTERS dict.

    Returns:
        YTM as an annualized percentage (e.g. 3.45 for 3.45%), or None if
        the inputs are invalid (past maturity, non-positive price/nominal)
        or the solver fails to converge.
    """
    if maturity_date <= settlement_date:
        return None
    if clean_price_pct <= 0 or nominal_value <= 0:
        return None

    day_counter = DAY_COUNTERS[day_count]
    ql_freq = FREQUENCIES[frequency]

    ql_settlement = _to_ql_date(settlement_date)
    ql_maturity = _to_ql_date(maturity_date)

    ql.Settings.instance().evaluationDate = ql_settlement

    schedule = ql.Schedule(
        ql_settlement,
        ql_maturity,
        ql.Period(ql_freq),
        ql.NullCalendar(),
        ql.Unadjusted,
        ql.Unadjusted,
        ql.DateGeneration.Backward,
        False,
    )

    try:
        bond = ql.FixedRateBond(
            0,                       # settlement days
            nominal_value,           # face amount
            schedule,
            [fixed_rate / 100.0],    # coupon as decimal
            day_counter,
        )
        bond_price = ql.BondPrice(clean_price_pct, ql.BondPrice.Clean)
        ytm = bond.bondYield(
            bond_price,
            day_counter,
            ql.Compounded,
            ql_freq,
            ql_settlement,
        )
    except RuntimeError:
        return None

    return ytm * 100.0
