from __future__ import annotations

import argparse
import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
KST = timezone(timedelta(hours=9), name="KST")
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={range}&interval={interval}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect OpenBell market data")
    parser.add_argument("--output", type=Path, default=Path("market_data.json"))
    args = parser.parse_args()

    generated_at = datetime.now(KST)
    report_date = generated_at.date()
    nasdaq = _chart("NQ=F", "5d", "5m")
    usdkrw = _chart("KRW=X", "5d", "1h")
    us10y = _chart("^TNX", "5d", "1h")
    sk_hynix_adr = _chart("SKHY", "5d", "1h")
    nvidia = _chart("NVDA", "5d", "1h")
    micron = _chart("MU", "5d", "1h")

    intraday = _nasdaq_morning_change(nasdaq, report_date)
    result = {
        "date": report_date.isoformat(),
        "generated_at": generated_at.strftime("%Y-%m-%d %H:%M"),
        "nasdaq100_futures_change_0700_0830_pct": intraday,
        "nasdaq100_futures_overnight_change_pct": _change_from_previous_close(nasdaq),
        "usdkrw_change_pct": _change_from_previous_close(usdkrw),
        "us10y_yield_change_pctp": _point_change_from_previous_close(us10y),
        "sk_hynix_adr_change_pct": _change_from_previous_close(sk_hynix_adr),
        "nvidia_change_pct": _change_from_previous_close(nvidia),
        "micron_change_pct": _change_from_previous_close(micron),
        # These fields are not exposed by Yahoo's public chart endpoint.
        # null makes the report exclude them instead of treating them as zero.
        "foreign_kospi200_futures_net_contracts": None,
        "foreign_put_options_net_contracts": None,
        "foreign_call_options_net_contracts": None,
        "program_net_buy_krw_100m": None,
        "investment_trust_futures_net_contracts": None,
        "put_option_iv_change_pct": None,
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _chart(symbol: str, chart_range: str, interval: str) -> dict:
    url = YAHOO_CHART_URL.format(symbol=quote(symbol, safe=""), range=chart_range, interval=interval)
    request = Request(url, headers={"User-Agent": "OpenBell-AI/1.0"})
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    chart = payload.get("chart", {})
    error = chart.get("error")
    if error:
        raise RuntimeError(f"Yahoo Finance {symbol}: {error.get('description', error)}")
    result = chart.get("result")
    if not result:
        raise RuntimeError(f"Yahoo Finance {symbol}: empty response")
    return result[0]


def _closes(chart: dict) -> list[tuple[datetime, float]]:
    timestamps = chart.get("timestamp", [])
    quotes = chart.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    values = []
    for timestamp, close in zip(timestamps, quotes):
        if close is not None:
            values.append((datetime.fromtimestamp(timestamp, timezone.utc).astimezone(KST), float(close)))
    if not values:
        raise RuntimeError("Yahoo Finance returned no closing prices")
    return values


def _previous_close(chart: dict) -> float:
    value = chart.get("meta", {}).get("previousClose")
    if value is None:
        raise RuntimeError("Yahoo Finance returned no previous close")
    return float(value)


def _change_from_previous_close(chart: dict) -> float:
    _, latest = _closes(chart)[-1]
    return round((latest / _previous_close(chart) - 1) * 100, 4)


def _point_change_from_previous_close(chart: dict) -> float:
    _, latest = _closes(chart)[-1]
    return round(latest - _previous_close(chart), 4)


def _nasdaq_morning_change(chart: dict, report_date: date) -> float:
    start = datetime.combine(report_date, time(7, 0), tzinfo=KST)
    end = datetime.combine(report_date, time(8, 30), tzinfo=KST)
    values = [(at, price) for at, price in _closes(chart) if start <= at <= end]
    if len(values) < 2:
        raise RuntimeError(f"Yahoo Finance NQ=F has insufficient 07:00-08:30 KST data for {report_date}")
    return round((values[-1][1] / values[0][1] - 1) * 100, 4)


if __name__ == "__main__":
    raise SystemExit(main())
