"""Compare saved benchmark runs without calling any model or API.

Use one comparison per input PDF. Optional --gold uses the Bilan JSON format.
"""
import argparse
import csv
import json
import statistics
import unicodedata
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def index_rows(document):
    counts = defaultdict(int)
    rows = {}
    for row in document["lignes"]:
        label = "|".join(row[field] for field in ("cote", "rubrique", "poste"))
        label = " ".join(unicodedata.normalize("NFKC", label).casefold().split())
        counts[label] += 1
        rows[(label, counts[label])] = row
    return rows


def amounts_equal(left, right):
    if left is None or right is None:
        return left is right
    try:
        a, b = Decimal(left), Decimal(right)
        return a.is_finite() and b.is_finite() and a == b
    except (InvalidOperation, TypeError, ValueError):
        return False


def score(reference, prediction):
    expected = index_rows(reference)
    actual = index_rows(prediction) if prediction else {}
    matched = expected.keys() & actual.keys()
    columns = ("montant_net_N", "montant_net_N1")
    numeric_count = sum(row[c] is not None for row in expected.values() for c in columns)
    correct = sum(amounts_equal(expected[k][c], actual[k][c])
                  for k in matched for c in columns)
    numeric_correct = sum(expected[k][c] is not None
                          and amounts_equal(expected[k][c], actual[k][c])
                          for k in matched for c in columns)
    return {
        "row_recall": len(matched) / len(expected),
        "row_precision": len(matched) / len(actual) if actual else 0,
        "cell_accuracy": correct / (2 * len(expected)),
        "numeric_accuracy": numeric_correct / numeric_count if numeric_count else None,
        "metadata_accuracy": sum(prediction is not None and prediction.get(k) == reference[k]
                                 for k in ("unite", "exercice_N", "exercice_N1")) / 3,
    }


def mean(values):
    values = [value for value in values if value is not None]
    return statistics.mean(values) if values else None


def compare(run_dirs, gold=None):
    """Return summaries grouped by run directory and model. Does not write files."""
    reference = read_json(Path(gold)) if gold else None
    if reference is not None and not reference.get("lignes"):
        raise ValueError("The human reference must contain annotated rows.")
    groups = defaultdict(list)
    for directory in run_dirs:
        directory = Path(directory)
        paths = sorted(directory.glob("*.metrics.json"))
        legacy = directory / "metrics.json"
        if legacy.exists():
            paths.append(legacy)
        if not paths:
            raise ValueError(f"No benchmark metrics found in {directory}")
        for path in paths:
            metrics = read_json(path)
            extraction = (directory / "extraction.json" if path.name == "metrics.json"
                          else path.with_name(path.name.replace(".metrics.json", ".json")))
            if reference is not None:
                prediction = None
                if metrics.get("valid_schema"):
                    if not extraction.exists():
                        raise FileNotFoundError(f"Missing extraction: {extraction}")
                    prediction = read_json(extraction)
                metrics.update(score(reference, prediction))
            groups[(str(directory), metrics["model"])].append(metrics)
    summaries = []
    for (directory, model), runs in groups.items():
        successful = [r for r in runs if r.get("valid_schema") and not r.get("error")]
        costs = [r.get("cost_usd_estimate") for r in runs]
        row = {
            "directory": directory,
            "model": model,
            "attempts": len(runs),
            "request_errors": sum(bool(r.get("error")) for r in runs),
            "json_valid_rate": mean([bool(r.get("valid_json")) for r in runs]),
            "schema_valid_rate": mean([bool(r.get("valid_schema")) for r in runs]),
            "latency_median_all_s": statistics.median(r["latency_seconds"] for r in runs),
            "latency_median_success_s": (statistics.median(r["latency_seconds"]
                                                       for r in successful) if successful else None),
            "input_tokens_mean": mean([r.get("input_tokens") for r in runs]),
            "output_tokens_mean": mean([r.get("output_tokens") for r in runs]),
            "cost_known_attempts": sum(c is not None for c in costs),
            "cost_mean_known_usd": mean(costs),
            "cost_total_usd": sum(costs) if all(c is not None for c in costs) else None,
        }
        if reference is not None:
            for metric in ("row_recall", "row_precision", "cell_accuracy",
                           "numeric_accuracy", "metadata_accuracy"):
                row[metric] = mean([r[metric] for r in runs])
        summaries.append(row)
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", required=True, help="Folders for the SAME PDF")
    parser.add_argument("--gold", help="Human-annotated Bilan JSON for that PDF")
    parser.add_argument("--out", default="results/comparison", help="New output directory")
    args = parser.parse_args()
    summaries = compare(args.runs, args.gold)
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "comparison.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    (output / "comparison.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved comparison.csv and comparison.json in {output}")
    if not args.gold:
        print("Accuracy was not measured: provide --gold with a human annotation.")
    print("Rates are 0–1. Blank costs are unknown, not zero. Compare the same PDF only.")
    print("Label matching uses side + section + label + occurrence; review label mismatches.")
    print("Cold and warm local runs should be compared in separate folders.")


if __name__ == "__main__":
    main()
