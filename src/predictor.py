from __future__ import annotations

from dataclasses import dataclass

from data_loader import MarketData


DISCLAIMER = (
    "본 결과는 투자 조언이 아니며, 제한된 입력값을 이용한 참고용 룰 기반 예측입니다. "
    "최종 투자 판단과 책임은 투자자 본인에게 있습니다."
)


@dataclass(frozen=True)
class ScoreItem:
    label: str
    score: int | None
    reason: str


@dataclass(frozen=True)
class ReferenceItem:
    label: str
    value: float | None
    unit: str
    reason: str


@dataclass(frozen=True)
class PredictionResult:
    total_score: int
    prediction: str
    risk_level: str
    score_items: list[ScoreItem]
    reference_items: list[ReferenceItem]
    checkpoints: list[str]
    disclaimer: str = DISCLAIMER


def predict(data: MarketData) -> PredictionResult:
    items = _score_items(data)
    total_score = sum(item.score for item in items if item.score is not None)

    return PredictionResult(
        total_score=total_score,
        prediction=classify_prediction(total_score),
        risk_level=classify_risk_level(total_score),
        score_items=items,
        reference_items=build_reference_items(data),
        checkpoints=build_checkpoints(data, total_score),
    )


def classify_prediction(score: int) -> str:
    if score <= -7:
        return "강한 갭하락 및 숏감마/급락 리스크"
    if score <= -3:
        return "갭하락 우위"
    if score >= 5:
        return "갭상승 우위"
    return "중립 또는 박스권 가능성"


def classify_risk_level(score: int) -> str:
    if score <= -7:
        return "매우 높음"
    if score <= -3:
        return "높음"
    if score >= 5:
        return "상방 우위"
    return "보통"


def build_checkpoints(data: MarketData, score: int) -> list[str]:
    checkpoints = [
        "08:30 이후 나스닥100 선물 반전 여부 확인",
        "원/달러 환율 추가 상승과 외국인 현물 매도 동반 여부 확인",
        "KOSPI200 선물 베이시스와 프로그램 매매 방향 확인",
        "풋옵션 IV 급등 지속 여부와 장초반 변동성 확대 여부 확인",
    ]
    if score <= -7:
        checkpoints.append("시초가 이후 반대매매성 매물과 하락 추세 지속 여부를 우선 점검")
    if data.foreign_call_options_net_contracts is not None and data.foreign_call_options_net_contracts > 0:
        checkpoints.append("외국인 콜옵션 순매수는 하락 압력을 일부 완화할 수 있음")
    return checkpoints


def build_reference_items(data: MarketData) -> list[ReferenceItem]:
    return [
        _reference("삼성전자", data.samsung_electronics_change_pct, "%", "Yahoo Finance 005930.KS 기준 생성 시점 등락률"),
        _reference("SK하이닉스", data.sk_hynix_change_pct, "%", "Yahoo Finance 000660.KS 기준 생성 시점 등락률"),
        _reference("SK하이닉스 ADR", data.sk_hynix_adr_change_pct, "%", "Yahoo Finance SKHY 기준 최근 등락률"),
        _reference("엔비디아", data.nvidia_change_pct, "%", "Yahoo Finance NVDA 기준 최근 등락률"),
        _reference("마이크론", data.micron_change_pct, "%", "Yahoo Finance MU 기준 최근 등락률"),
    ]


def _score_items(data: MarketData) -> list[ScoreItem]:
    items: list[ScoreItem] = []

    if data.nasdaq100_futures_change_0700_0830_pct is None:
        items.append(_unavailable("나스닥100 선물 07:00~08:30"))
    elif data.nasdaq100_futures_change_0700_0830_pct <= -1.0:
        items.append(_item("나스닥100 선물 07:00~08:30", -3, f"{data.nasdaq100_futures_change_0700_0830_pct:.2f}% <= -1.0%"))
    elif data.nasdaq100_futures_change_0700_0830_pct >= 1.0:
        items.append(_item("나스닥100 선물 07:00~08:30", 3, f"{data.nasdaq100_futures_change_0700_0830_pct:.2f}% >= +1.0%"))
    else:
        items.append(_item("나스닥100 선물 07:00~08:30", 0, f"{data.nasdaq100_futures_change_0700_0830_pct:.2f}%로 임계값 미충족"))

    if data.nasdaq100_futures_overnight_change_pct is None:
        items.append(_unavailable("나스닥100 선물 야간"))
    elif data.nasdaq100_futures_overnight_change_pct <= -2.0:
        items.append(_item("나스닥100 선물 야간", -2, f"{data.nasdaq100_futures_overnight_change_pct:.2f}% <= -2.0%"))
    elif data.nasdaq100_futures_overnight_change_pct >= 2.0:
        items.append(_item("나스닥100 선물 야간", 2, f"{data.nasdaq100_futures_overnight_change_pct:.2f}% >= +2.0%"))
    else:
        items.append(_item("나스닥100 선물 야간", 0, f"{data.nasdaq100_futures_overnight_change_pct:.2f}%로 임계값 미충족"))

    if data.usdkrw_change_pct is None:
        items.append(_unavailable("원/달러 환율"))
    elif data.usdkrw_change_pct > 0.5:
        items.append(_item("원/달러 환율", -1, f"{data.usdkrw_change_pct:.2f}% > +0.5%"))
    else:
        items.append(_item("원/달러 환율", 0, f"{data.usdkrw_change_pct:.2f}%로 임계값 미충족"))

    if data.us10y_yield_change_pctp is None:
        items.append(_unavailable("미국 10년물 금리"))
    elif data.us10y_yield_change_pctp > 0.05:
        items.append(_item("미국 10년물 금리", -1, f"{data.us10y_yield_change_pctp:.2f}%p > +0.05%p"))
    else:
        items.append(_item("미국 10년물 금리", 0, f"{data.us10y_yield_change_pctp:.2f}%p로 임계값 미충족"))

    if data.foreign_kospi200_futures_net_contracts is None:
        items.append(_unavailable("외국인 KOSPI200 선물"))
    elif data.foreign_kospi200_futures_net_contracts < -5000:
        items.append(_item("외국인 KOSPI200 선물", -2, f"{data.foreign_kospi200_futures_net_contracts:,}계약 < -5,000계약"))
    elif data.foreign_kospi200_futures_net_contracts > 5000:
        items.append(_item("외국인 KOSPI200 선물", 2, f"{data.foreign_kospi200_futures_net_contracts:,}계약 > +5,000계약"))
    else:
        items.append(_item("외국인 KOSPI200 선물", 0, f"{data.foreign_kospi200_futures_net_contracts:,}계약으로 임계값 미충족"))

    if data.foreign_put_options_net_contracts is None or data.put_option_iv_change_pct is None:
        items.append(_unavailable("외국인 풋옵션 + 풋 IV"))
    elif data.foreign_put_options_net_contracts < -10000 and data.put_option_iv_change_pct > 25:
        items.append(_item("외국인 풋옵션 + 풋 IV", -3, f"풋 {data.foreign_put_options_net_contracts:,}계약 < -10,000계약, IV {data.put_option_iv_change_pct:.2f}% > 25%"))
    else:
        items.append(_item("외국인 풋옵션 + 풋 IV", 0, f"풋 {data.foreign_put_options_net_contracts:,}계약, IV {data.put_option_iv_change_pct:.2f}%로 복합 조건 미충족"))

    if data.program_net_buy_krw_100m is None:
        items.append(_unavailable("프로그램 매매"))
    elif data.program_net_buy_krw_100m < -3000:
        items.append(_item("프로그램 매매", -1, f"{data.program_net_buy_krw_100m:,}억 원 < -3,000억 원"))
    else:
        items.append(_item("프로그램 매매", 0, f"{data.program_net_buy_krw_100m:,}억 원으로 임계값 미충족"))

    if data.investment_trust_futures_net_contracts is None:
        items.append(_unavailable("투신 선물"))
    elif data.investment_trust_futures_net_contracts < -5000:
        items.append(_item("투신 선물", -1, f"{data.investment_trust_futures_net_contracts:,}계약 < -5,000계약"))
    else:
        items.append(_item("투신 선물", 0, f"{data.investment_trust_futures_net_contracts:,}계약으로 임계값 미충족"))

    return items


def _item(label: str, score: int, reason: str) -> ScoreItem:
    return ScoreItem(label=label, score=score, reason=reason)


def _unavailable(label: str) -> ScoreItem:
    return ScoreItem(label=label, score=None, reason="최신 공개 데이터 미수집 · 점수에서 제외")


def _reference(label: str, value: float | None, unit: str, reason: str) -> ReferenceItem:
    return ReferenceItem(label=label, value=value, unit=unit, reason=reason)
