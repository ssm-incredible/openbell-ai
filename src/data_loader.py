from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MarketData:
    date: date
    nasdaq100_futures_change_0700_0830_pct: float
    nasdaq100_futures_overnight_change_pct: float
    usdkrw_change_pct: float
    us10y_yield_change_pctp: float
    foreign_kospi200_futures_net_contracts: int
    foreign_put_options_net_contracts: int
    foreign_call_options_net_contracts: int
    program_net_buy_krw_100m: int
    investment_trust_futures_net_contracts: int
    put_option_iv_change_pct: float


REQUIRED_FIELDS = set(MarketData.__dataclass_fields__)


def load_market_data(path: str | Path) -> MarketData:
    data_path = Path(path)
    if not data_path.exists():
        raise FileNotFoundError(f"data file not found: {data_path}")

    try:
        raw = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {data_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError("data file must contain a JSON object")

    missing = REQUIRED_FIELDS - raw.keys()
    if missing:
        raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")

    # TODO: Replace this JSON loader with real market data APIs.
    return MarketData(
        date=_parse_date(raw["date"]),
        nasdaq100_futures_change_0700_0830_pct=_to_float(raw, "nasdaq100_futures_change_0700_0830_pct"),
        nasdaq100_futures_overnight_change_pct=_to_float(raw, "nasdaq100_futures_overnight_change_pct"),
        usdkrw_change_pct=_to_float(raw, "usdkrw_change_pct"),
        us10y_yield_change_pctp=_to_float(raw, "us10y_yield_change_pctp"),
        foreign_kospi200_futures_net_contracts=_to_int(raw, "foreign_kospi200_futures_net_contracts"),
        foreign_put_options_net_contracts=_to_int(raw, "foreign_put_options_net_contracts"),
        foreign_call_options_net_contracts=_to_int(raw, "foreign_call_options_net_contracts"),
        program_net_buy_krw_100m=_to_int(raw, "program_net_buy_krw_100m"),
        investment_trust_futures_net_contracts=_to_int(raw, "investment_trust_futures_net_contracts"),
        put_option_iv_change_pct=_to_float(raw, "put_option_iv_change_pct"),
    )


def _parse_date(value: Any) -> date:
    if not isinstance(value, str):
        raise ValueError("date must be a YYYY-MM-DD string")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("date must be a valid YYYY-MM-DD string") from exc


def _to_float(raw: dict[str, Any], key: str) -> float:
    try:
        return float(raw[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a number") from exc


def _to_int(raw: dict[str, Any], key: str) -> int:
    value = raw[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc
