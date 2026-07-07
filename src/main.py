from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data_loader import load_market_data
from html_report import write_html_report
from predictor import PredictionResult, predict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "sample_data.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "result.html"


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenBell AI domestic pre-market predictor")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="input JSON path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="HTML report output path")
    args = parser.parse_args()

    try:
        data = load_market_data(args.data)
        result = predict(data)
        write_html_report(data, result, args.output)
    except Exception as exc:
        print(f"OpenBell AI error: {exc}", file=sys.stderr)
        return 1

    print_cli_report(data.date.isoformat(), result, args.output)
    return 0


def print_cli_report(report_date: str, result: PredictionResult, output_path: Path) -> None:
    print("OpenBell AI")
    print("=" * 48)
    print(f"날짜: {report_date}")
    print(f"총점: {result.total_score:+d}")
    print(f"예측 결과: {result.prediction}")
    print(f"위험등급: {result.risk_level}")
    print()
    print("각 점수 항목별 근거")
    for item in result.score_items:
        print(f"- {item.label}: {item.score:+d}점 ({item.reason})")
    print()
    print("장전 체크포인트")
    for checkpoint in result.checkpoints:
        print(f"- {checkpoint}")
    print()
    print("투자 주의 문구")
    print(result.disclaimer)
    print()
    print(f"HTML 리포트 생성: {output_path}")


if __name__ == "__main__":
    raise SystemExit(main())
