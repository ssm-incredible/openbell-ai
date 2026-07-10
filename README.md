# OpenBell AI

국내 증시 개장 전 미국 나스닥100 선물 흐름과 국내 파생/수급 데이터를 기반으로 KOSPI/KOSPI200 시초가 방향과 장중 리스크를 예측하는 Python 프로그램입니다.

GitHub Actions가 매 영업일 장 시작 전에 Yahoo Finance 공개 시세 API에서 최신 데이터를 수집하고 룰 기반 점수를 계산합니다.

## 실행 환경

- Python 3.11
- 외부 Python 패키지 없음

## 설치 및 실행

```bash
cd openbell-ai
python -m pip install -r requirements.txt
python src/main.py
```

다른 데이터 파일을 쓰려면 다음처럼 실행합니다.

```bash
python src/main.py --data sample_data.json --output result.html
```

실행하면 CLI에 예측 결과가 출력되고, 같은 폴더에 `result.html` 리포트가 생성됩니다.

최신 데이터 수집을 수동 실행하려면 다음처럼 실행합니다.

```bash
python src/collect_market_data.py --output market_data.json
python src/main.py --data market_data.json --output result.html
```

## 입력 데이터

`sample_data.json` 필드:

- `date`: 기준 날짜, `YYYY-MM-DD`
- `nasdaq100_futures_change_0700_0830_pct`: 나스닥100 선물 07:00~08:30 변동률
- `nasdaq100_futures_overnight_change_pct`: 나스닥100 선물 야간 변동률
- `usdkrw_change_pct`: 원/달러 환율 변화율
- `us10y_yield_change_pctp`: 미국 10년물 금리 변화, %p
- `foreign_kospi200_futures_net_contracts`: 외국인 KOSPI200 선물 순매수 계약 수
- `foreign_put_options_net_contracts`: 외국인 풋옵션 순매수 계약 수
- `foreign_call_options_net_contracts`: 외국인 콜옵션 순매수 계약 수
- `program_net_buy_krw_100m`: 프로그램 순매수 금액, 억 원
- `investment_trust_futures_net_contracts`: 투신 선물 순매수 계약 수
- `put_option_iv_change_pct`: 풋옵션 IV 상승률

순매도 값은 음수로 입력합니다.

## 점수 모델

- 나스닥100 선물 07:00~08:30 변동률이 -1.0% 이하이면 -3점
- 나스닥100 선물 07:00~08:30 변동률이 +1.0% 이상이면 +3점
- 나스닥100 선물 야간 변동률이 -2.0% 이하이면 -2점
- 나스닥100 선물 야간 변동률이 +2.0% 이상이면 +2점
- 원/달러 환율 변화율이 +0.5% 초과이면 -1점
- 미국 10년물 금리 변화가 +0.05%p 초과이면 -1점
- 외국인 KOSPI200 선물 순매도가 -5,000계약 미만이면 -2점
- 외국인 KOSPI200 선물 순매수가 +5,000계약 초과이면 +2점
- 외국인 풋옵션 순매도가 -10,000계약 미만이고 풋 IV 상승률이 25% 초과이면 -3점
- 프로그램 순매도가 -3,000억 원 미만이면 -1점
- 투신 선물 순매도가 -5,000계약 미만이면 -1점

## 결과 분류

- `score <= -7`: 강한 갭하락 및 숏감마/급락 리스크
- `score <= -3`: 갭하락 우위
- `score >= 5`: 갭상승 우위
- 그 외: 중립 또는 박스권 가능성

## 최신 데이터 수집

`src/collect_market_data.py`는 다음 Yahoo Finance 심볼을 사용합니다.

- `NQ=F`: 나스닥100 선물
- `KRW=X`: 원/달러 환율
- `^TNX`: 미국 10년물 금리

Yahoo Finance 공개 차트 API에서 제공하지 않는 국내 외국인 선물·옵션, 프로그램 매매, 투신 선물 데이터는 `null`로 기록하고 점수에서 제외합니다. 리포트에는 해당 항목이 `최신 공개 데이터 미수집`으로 표시됩니다.

## GitHub Actions

`.github/workflows/daily.yml`은 평일 한국시간 오전 8:30에 실행되도록 구성되어 있습니다.

한국시간 `08:30`은 UTC 기준 전날 `23:30`이므로 cron은 다음과 같습니다.

```yaml
cron: "30 23 * * 0-4"
```

워크플로는 Python 3.11을 설치하고 최신 데이터를 수집한 뒤 프로그램을 실행합니다. 생성된 `result.html`은 artifact로 저장되며, `main` 브랜치에서는 GitHub Pages로 배포됩니다.

## 투자 주의 문구

본 결과는 투자 조언이 아니며, 제한된 입력값을 이용한 참고용 룰 기반 예측입니다. 최종 투자 판단과 책임은 투자자 본인에게 있습니다.

## 향후 작업

- 입력 데이터 검증 강화
- 과거 데이터 기반 점수 임계값 검증
