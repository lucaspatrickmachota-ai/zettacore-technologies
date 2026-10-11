"""Offline synthetic benchmark. Do not interpret results as real-world accuracy."""
import json
from pathlib import Path

from app.main import analyze

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests" / "fixtures" / "url_cases.json").read_text(encoding="utf-8"))


def main():
    tp = fp = tn = fn = 0
    errors = []
    for label, urls in (("legitimate", CASES["legitimate"]), ("synthetic_suspicious", CASES["synthetic_suspicious"])):
        expected_suspicious = label == "synthetic_suspicious"
        for url in urls:
            result = analyze(url)
            predicted_suspicious = bool(result["findings"])
            if expected_suspicious and predicted_suspicious:
                tp += 1
            elif expected_suspicious and not predicted_suspicious:
                fn += 1
                errors.append(("false_negative", url))
            elif not expected_suspicious and predicted_suspicious:
                fp += 1
                errors.append(("false_positive", url))
            else:
                tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    print("SYNTHETIC OFFLINE CORPUS — NOT REAL-WORLD ACCURACY")
    print(f"TP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"Precision on this corpus: {precision:.1%}")
    print(f"Recall on this corpus:    {recall:.1%}")
    print(f"Cases: {len(CASES['legitimate'])} labelled legitimate; {len(CASES['synthetic_suspicious'])} synthetic suspicious")
    for kind, url in errors:
        print(f"{kind}: {url}")


if __name__ == "__main__":
    main()
