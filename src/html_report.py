from __future__ import annotations

from html import escape
from pathlib import Path

from data_loader import MarketData
from predictor import PredictionResult


def write_html_report(data: MarketData, result: PredictionResult, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.write_text(render_html(data, result), encoding="utf-8")
    return path


def render_html(data: MarketData, result: PredictionResult) -> str:
    score_class = _score_class(result.total_score)
    items = "\n".join(
        f"""
        <li>
          <span>
            <strong>{escape(item.label)}</strong>
            <small>{escape(item.reason)}</small>
          </span>
          <b class="{_score_class(item.score)}">{_score_text(item.score)}</b>
        </li>
        """
        for item in result.score_items
    )
    checkpoints = "\n".join(f"<li>{escape(checkpoint)}</li>" for checkpoint in result.checkpoints)
    reference_items = "\n".join(
        f"""
        <li>
          <span>
            <strong>{escape(item.label)}</strong>
            <small>{escape(item.reason)}</small>
          </span>
          <b class="{_value_class(item.value)}">{_value_text(item.value, item.unit)}</b>
        </li>
        """
        for item in result.reference_items
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OpenBell AI - {data.generated_at.strftime("%Y-%m-%d %H:%M")}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7fb;
      --card: #ffffff;
      --text: #172033;
      --muted: #667085;
      --border: #d9e0ec;
      --good: #0f7a45;
      --bad: #b42318;
      --neutral: #344054;
      --accent: #1d4ed8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    main {{
      width: min(1040px, 100%);
      margin: 0 auto;
      padding: 28px 18px;
    }}
    header {{
      display: grid;
      gap: 8px;
      margin-bottom: 18px;
    }}
    h1, h2, p {{ margin: 0; }}
    h1 {{ font-size: clamp(28px, 5vw, 44px); letter-spacing: 0; }}
    h2 {{ font-size: 18px; }}
    .subtitle {{ color: var(--muted); }}
    .grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 16px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 10px 26px rgba(23, 32, 51, 0.06);
    }}
    .summary {{
      display: grid;
      grid-template-columns: auto 1fr;
      align-items: center;
      gap: 18px;
    }}
    .score {{
      display: grid;
      place-items: center;
      width: 112px;
      height: 112px;
      border-radius: 8px;
      font-size: 36px;
      font-weight: 800;
      background: #eef4ff;
      color: var(--accent);
    }}
    .positive {{ color: var(--good); }}
    .negative {{ color: var(--bad); }}
    .neutral {{ color: var(--neutral); }}
    .prediction {{ font-size: clamp(24px, 4vw, 34px); font-weight: 800; }}
    .risk {{ margin-top: 8px; color: var(--muted); }}
    ul {{ list-style: none; margin: 14px 0 0; padding: 0; }}
    .items li {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      padding: 13px 0;
      border-bottom: 1px solid var(--border);
    }}
    .items li:last-child {{ border-bottom: 0; }}
    .items b {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 58px;
      padding: 4px 9px;
      border-radius: 8px;
      font-size: 17px;
      font-weight: 900;
      background: #eef4ff;
      color: var(--accent);
      white-space: nowrap;
    }}
    .items b.positive {{ background: #e9f9f0; color: var(--good); }}
    .items b.negative {{ background: #fff1f0; color: var(--bad); }}
    .items b.neutral {{ background: #eef4ff; color: var(--accent); }}
    small {{ display: block; margin-top: 3px; color: var(--muted); }}
    .checkpoints li {{
      padding: 10px 0 10px 18px;
      border-bottom: 1px solid var(--border);
      position: relative;
    }}
    .checkpoints li:before {{
      content: "";
      width: 6px;
      height: 6px;
      border-radius: 999px;
      background: var(--accent);
      position: absolute;
      left: 0;
      top: 18px;
    }}
    .disclaimer {{
      margin-top: 16px;
      border-color: #f2c94c;
      background: #fff9e8;
    }}
    @media (max-width: 760px) {{
      main {{ padding: 20px 14px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .summary {{ grid-template-columns: 1fr; }}
      .score {{ width: 100%; height: auto; padding: 18px; }}
      .items li {{ align-items: flex-start; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>OpenBell AI</h1>
      <p class="subtitle">국내 증시 장전 룰 기반 예측 리포트 · 기준일 {data.date.isoformat()} · 생성 {data.generated_at.strftime("%Y-%m-%d %H:%M")}</p>
    </header>

    <section class="card summary">
      <div class="score {score_class}">{result.total_score:+d}</div>
      <div>
        <p class="prediction">{escape(result.prediction)}</p>
        <p class="risk">위험등급: <strong>{escape(result.risk_level)}</strong></p>
      </div>
    </section>

    <div class="grid" style="margin-top:16px">
      <section class="card">
        <h2>점수 근거</h2>
        <ul class="items">{items}</ul>
      </section>
      <section class="card">
        <h2>반도체 참고 지표</h2>
        <ul class="items market-items">{reference_items}</ul>
      </section>
    </div>

    <section class="card" style="margin-top:16px">
      <h2>장전 체크포인트</h2>
      <ul class="checkpoints">{checkpoints}</ul>
    </section>

    <section class="card disclaimer">
      <h2>투자 주의 문구</h2>
      <p>{escape(result.disclaimer)}</p>
    </section>
  </main>
</body>
</html>
"""


def _score_text(score: int | None) -> str:
    return "—" if score is None else f"{score:+d}"


def _score_class(score: int | None) -> str:
    if score is None:
        return "neutral"
    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def _value_text(value: float | None, unit: str) -> str:
    if value is None:
        return "미수집"
    return f"{value:+.2f}{unit}"


def _value_class(value: float | None) -> str:
    if value is None:
        return "neutral"
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"
