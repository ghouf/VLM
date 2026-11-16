"""Compare une référence annotée et une extraction GPT, sans appel API.

Exemple : python src/vlm/evaluate_lines.py --gold data/gold/bilan10_brut_amort_net.json
          --prediction results/gpt-brut-amort-net-01/run_01.json --out results/lignes-01
"""
import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


AMOUNTS = (
    "montant_net_N", "montant_net_N1", "montant_brut_N",
    "montant_amort_prov_N", "montant_brut_N1", "montant_amort_prov_N1",
)
METADATA = ("unite", "exercice_N", "exercice_N1")


def normalize(value):
    """Ignore casse, accents, ponctuation et espaces pour apparier les libellés."""
    text = unicodedata.normalize("NFKD", value).casefold()
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w]+", " ", text).split())


def read_document(path):
    document = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(document, dict) or not isinstance(document.get("lignes"), list):
        raise ValueError(f"{path}: objet JSON avec une liste 'lignes' attendu")
    for index, row in enumerate(document["lignes"], 1):
        if not isinstance(row, dict) or any(
            not isinstance(row.get(k), str) for k in ("cote", "rubrique", "poste", "type_ligne")
        ):
            raise ValueError(f"{path}: ligne {index} invalide")
    return document


def number(value):
    # Les extractions doivent déjà suivre le format décimal du schéma.
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except InvalidOperation:
        return None


def equal_amount(expected, actual, tolerance):
    if expected is None or actual is None:
        return expected is actual
    left, right = number(expected), number(actual)
    return left is not None and right is not None and abs(left - right) <= tolerance


def match_rows(reference, prediction):
    """Appariement exact normalisé, puis poste unique du même côté.

    Aucun rapprochement flou ni rapprochement basé sur les montants.
    Les doublons exacts sont appariés dans leur ordre d'apparition.
    """
    available = set(range(len(prediction)))
    buckets = defaultdict(list)
    for j, row in enumerate(prediction):
        buckets[tuple(normalize(row[k]) for k in ("cote", "rubrique", "poste"))].append(j)
    matches = {}
    for i, row in enumerate(reference):
        key = tuple(normalize(row[k]) for k in ("cote", "rubrique", "poste"))
        if buckets[key]:
            j = buckets[key].pop(0)
            matches[i] = (j, "libelle_et_rubrique")
            available.remove(j)
    remaining = defaultdict(list)
    candidates = defaultdict(list)
    for i, row in enumerate(reference):
        if i not in matches:
            remaining[(normalize(row["cote"]), normalize(row["poste"]))].append(i)
    for j in sorted(available):
        row = prediction[j]
        candidates[(normalize(row["cote"]), normalize(row["poste"]))].append(j)
    for key, indices in remaining.items():
        if len(indices) == 1 and len(candidates[key]) == 1:
            i, j = indices[0], candidates[key][0]
            matches[i] = (j, "poste_unique_rubrique_a_verifier")
            available.remove(j)
    return matches, sorted(available)


def evaluate(reference, prediction, tolerance=Decimal("0")):
    expected, actual = reference["lignes"], prediction["lignes"]
    if not expected:
        raise ValueError("La référence ne contient aucune ligne")
    columns = [c for c in AMOUNTS if any(c in row for row in expected)]
    if not columns:
        raise ValueError("La référence ne contient aucune colonne de montants")
    matches, extras = match_rows(expected, actual)
    details, errors = [], []
    counts = {c: {"cells": len(expected), "correct": 0, "numeric_cells": 0,
                  "numeric_correct": 0} for c in columns}

    def error(category, i, j, field, left, right):
        errors.append({"categorie": category, "ligne_reference": i + 1 if i is not None else None,
                       "ligne_prediction": j + 1 if j is not None else None,
                       "champ": field, "attendu": left, "predit": right})

    for i, row in enumerate(expected):
        j, method = matches.get(i, (None, None))
        predicted = actual[j] if j is not None else {}
        record = {"ligne_reference": i + 1, "ligne_prediction": j + 1 if j is not None else None,
                  "cote": row["cote"], "rubrique": row["rubrique"], "poste": row["poste"],
                  "appariement": method, "prediction": predicted or None}
        before = len(errors)
        if j is None:
            error("ligne_manquante", i, None, "ligne", row, None)
        else:
            for field in ("rubrique", "type_ligne"):
                if normalize(row[field]) != normalize(predicted[field]):
                    error("structure", i, j, field, row[field], predicted[field])
        for column in columns:
            left, right = row.get(column), predicted.get(column)
            ok = j is not None and column in row and column in predicted and equal_amount(left, right, tolerance)
            numeric = number(left) is not None
            counts[column]["correct"] += int(ok)
            counts[column]["numeric_cells"] += int(numeric)
            counts[column]["numeric_correct"] += int(ok and numeric)
            record[column + "_attendu"] = left
            record[column + "_predit"] = right
            record[column + "_correct"] = ok
            if j is not None and not ok:
                category = "champ_absent" if column not in predicted or column not in row else "montant"
                error(category, i, j, column, left, right)
        record["statut"] = "manquante" if j is None else ("conforme" if len(errors) == before else "ecart")
        details.append(record)
    for j in extras:
        error("ligne_supplementaire", None, j, "ligne", None, actual[j])
    metadata_correct = 0
    for field in METADATA:
        ok = field in reference and field in prediction and reference[field] == prediction[field]
        metadata_correct += int(ok)
        if not ok:
            error("metadonnee", None, None, field, reference.get(field), prediction.get(field))
    for values in counts.values():
        values["accuracy"] = values["correct"] / values["cells"]
        values["numeric_accuracy"] = (values["numeric_correct"] / values["numeric_cells"]
                                      if values["numeric_cells"] else None)
    summary = {
        "reference_rows": len(expected), "prediction_rows": len(actual),
        "matched_rows": len(matches), "missing_rows": len(expected) - len(matches),
        "extra_rows": len(extras), "row_recall": len(matches) / len(expected),
        "row_precision": len(matches) / len(actual) if actual else 0,
        "complete_row_accuracy": sum(r["statut"] == "conforme" for r in details) / len(expected),
        "cell_accuracy": sum(v["correct"] for v in counts.values()) / (len(expected) * len(columns)),
        "metadata_accuracy": metadata_correct / len(METADATA),
        "tolerance": str(tolerance), "columns": counts,
        "matching": "Libellés normalisés; repli sur poste unique du même côté. Pas de fuzzy matching.",
    }
    return {"summary": summary, "lines": details, "errors": errors}


def write_csv(path, records):
    if not records:
        path.write_text("", encoding="utf-8-sig")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), delimiter=";")
        writer.writeheader()
        for row in records:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list))
                             else v for k, v in row.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, help="JSON de référence relu")
    parser.add_argument("--prediction", required=True, help="JSON extrait par GPT")
    parser.add_argument("--out", required=True, help="Nouveau dossier de sortie")
    parser.add_argument("--tolerance", default="0", help="Écart absolu accepté, dans l'unité du document")
    args = parser.parse_args()
    tolerance = number(args.tolerance)
    if tolerance is None or tolerance < 0:
        parser.error("--tolerance doit être un nombre fini positif ou nul")
    report = evaluate(read_document(args.gold), read_document(args.prediction), tolerance)
    report["sources"] = {"gold": args.gold, "prediction": args.prediction}
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(output / "lines.csv", report["lines"])
    write_csv(output / "errors.csv", report["errors"])
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"Rapport enregistré dans {output}")


if __name__ == "__main__":
    main()
