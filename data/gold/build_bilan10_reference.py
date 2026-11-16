"""Independent transcription checked against all three rendered PDF pages.

This builds reference data; it never reads model outputs or calls an API.
"""
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
rows = []
side = section = None


def group(cote, rubrique):
    global side, section
    side, section = cote, rubrique


def row(poste, kind="detail", net=None, previous=None, brut=None, amort=None):
    rows.append({
        "poste": poste, "rubrique": section, "cote": side, "type_ligne": kind,
        "montant_net_N": net, "montant_net_N1": previous,
        "montant_brut_N": brut, "montant_amort_prov_N": amort,
        "montant_brut_N1": None, "montant_amort_prov_N1": None,
    })


# PDF page 1 (printed page 2). Group rows are actual table rows;
# repeated labels in the merged left margin are not additional rows.
group("actif", "IMMOBILISATION EN NON VALEURS (A)")
row("Immobilisations en non valeurs (A)", "sous_total")
row("Frais préliminaires")
row("Charges à répartir sur plusieurs exercices")
row("Primes de remboursement des obligations")
group("actif", "IMMOBILISATIONS INCORPORELLES (B)")
row("Immobilisations incorporelles (B)", "sous_total")
row("Immobilisations en recherche et développement")
row("Brevets, marques, droits et valeurs similaires")
row("Fonds commercial")
row("Autres immobilisations incorporelles")
group("actif", "IMMOBILISATIONS CORPORELLES (C)")
row("Immobilisations corporelles (C)", "sous_total", "398608.33", "455050.73", "559924.00", "161315.67")
row("Terrains")
row("Constructions", net="125412.79", previous="143134.69", brut="177219.00", amort="51806.21")
row("Installations techniques, matériel et outillage", net="267938.55", previous="305309.05", brut="373705.00", amort="105766.45")
row("Matériel de transport")
row("Mobilier, Matériel de bureau et aménagement divers", net="5256.99", previous="6606.99", brut="9000.00", amort="3743.01")
row("Autres immobilisations corporelles")
row("Immobilisations corporelles en cours")
group("actif", "IMMOBILISATIONS FINANCIERES (D)")
row("Immobilisations financières (D)", "sous_total")
row("Prêts immobilisés")
row("Autres créances financières")
row("Titres de participation")
row("Autres titres immobilisés")
group("actif", "ECARTS DE CONVERSION - ACTIF (E)")
row("Ecarts de conversion actif (E)", "sous_total")
row("Diminution des créances immobilisées")
row("Augmentations des dettes de financement")
group("actif", "TOTAL I (A+B+C+D+E)")
row("TOTAL I (A+B+C+D+E)", "sous_total", "398608.33", "455050.73", "559924.00", "161315.67")

# PDF page 2 (printed page 3).
group("actif", "STOCKS (F)")
row("Stocks (F)", "sous_total", "221506.25", "290806.77", "221506.25")
row("Marchandises")
row("Matières et fournitures consommables", net="221506.25", previous="290806.77", brut="221506.25")
row("Produits en cours")
row("Produits intermédiaires et produits résiduels")
row("Produits finis")
group("actif", "CREANCES DE L'ACTIF CIRCULANT (G)")
row("Créances de l'actif circulant (G)", "sous_total", "2960041.51", "1707914.11", "2960041.51")
row("Fournis. débiteurs, avances et acomptes")
row("Clients et comptes rattachés", net="2462210.41", previous="1295962.86", brut="2462210.41")
row("Personnel", net="4000.00", previous="4000.00", brut="4000.00")
row("Etat", net="353831.10", previous="267951.25", brut="353831.10")
row("Comptes d'associés", net="100000.00", previous="100000.00", brut="100000.00")
row("Autres débiteurs", net="40000.00", previous="40000.00", brut="40000.00")
row("Comptes de régularisation- Actif")
group("actif", "TITRES VALEURS DE PLACEMENT (H)")
row("Titres valeurs de placement (H)", "sous_total")
group("actif", "ECARTS DE CONVERSION - ACTIF (I)")
row("Ecarts de conversion actif (I) Eléments circulants", "sous_total")
group("actif", "TOTAL II (F+G+H+I)")
row("TOTAL II (F+G+H+I)", "sous_total", "3181547.76", "1998720.88", "3181547.76")
group("actif", "TRESORERIE - ACTIF")
row("Trésorerie-Actif", "sous_total", "5637.63", "845.77", "5637.63")
row("Chèques et valeurs à encaisser")
row("Banques, T.G et C.C.P")
row("Caisse, Régie d'avances et accréditifs", net="5637.63", previous="845.77", brut="5637.63")
group("actif", "TOTAL III")
row("TOTAL III", "sous_total", "5637.63", "845.77", "5637.63")
group("actif", "TOTAL GENERAL I+II+III")
row("TOTAL GENERAL I+II+III", "total_general", "3585793.72", "2454617.38", "3747109.39", "161315.67")

# PDF page 3 (printed page 4).
group("passif", "CAPITAUX PROPRES (A)")
row("Capital social ou personnel (1)", net="100000.00", previous="100000.00")
row("Moins : actionnaires, capital souscrit non appelé")
row("Moins : Capital appelé", net="100000.00", previous="100000.00")
row("Moins : Dont versé")
row("Prime d'émission, de fusion, d'apport")
row("Ecarts de réévaluation")
row("Réserve légale")
row("Autres réserves")
row("Report à nouveau (2)", net="-483691.10", previous="-586830.31")
row("Résultats nets en instance d'affectation (2)")
row("Résultat net de l'exercice (2)", net="372505.36", previous="103139.21")
row("Total des capitaux propres (A)", "sous_total", "-11185.74", "-383691.10")
group("passif", "CAPITAUX PROPRES ASSIMILES (B)")
row("Capitaux propres assimilés (B)", "sous_total")
row("Subvention d'investissement")
row("Provisions réglementées")
group("passif", "DETTES DE FINANCEMENT (C)")
row("Dettes de financement (C)", "sous_total")
row("Emprunts obligataires")
row("Autres dettes de financement")
group("passif", "PROVISIONS DURABLES POUR RISQUES ET CHARGES (D)")
row("Provisions durables pour risques et charges (D)", "sous_total")
row("Provisions pour risques")
row("Provisions pour charges")
group("passif", "ECARTS DE CONVERSION - PASSIF (E)")
row("Ecarts de conversion-passif (E)", "sous_total")
row("Augmentation des créances immobilisées")
row("Diminution des dettes de financement")
group("passif", "TOTAL I (A+B+C+D+E)")
row("TOTAL I (A+B+C+D+E)", "sous_total", "-11185.74", "-383691.10")
group("passif", "DETTES DU PASSIF CIRCULANT (F)")
row("Dettes du passif circulant (F)", "sous_total", "2882234.28", "1828051.60")
row("Fournisseurs et comptes rattachés", net="1814187.07", previous="1109508.19")
row("Clients créditeurs, avances et acomptes")
row("Personnel", net="13236.59")
row("Organismes sociaux", net="21314.58", previous="35260.93")
row("Etat", net="983496.04", previous="613482.48")
row("Comptes d'associés")
row("Autres créanciers", net="50000.00", previous="69800.00")
row("Comptes de régularisation passif")
group("passif", "AUTRES PROVISIONS POUR RISQUES ET CHARGES (G)")
row("Autres provisions pour risques et charges (G)", "sous_total")
group("passif", "ECARTS DE CONVERSION - PASSIF (ELEMENTS CIRCULANTS) (H)")
row("Ecarts de conversion - passif (Eléments circulants) (H)", "sous_total")
group("passif", "TOTAL II (F+G+H)")
row("TOTAL II (F+G+H)", "sous_total", "2882234.28", "1828051.60")
group("passif", "TRESORERIE - PASSIF")
row("Crédits d'escompte")
row("Crédits de trésorerie")
row("Banques (soldes créditeurs)", net="714745.18", previous="1010256.88")
group("passif", "TOTAL III")
row("TOTAL III", "sous_total", "714745.18", "1010256.88")
group("passif", "TOTAL GENERAL I+II+III")
row("TOTAL GENERAL I+II+III", "total_general", "3585793.72", "2454617.38")


def write(name, document):
    (OUT / name).write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    full = {"unite": "inconnue", "exercice_N": None, "exercice_N1": None, "lignes": rows}
    write("bilan10_brut_amort_net.json", full)
    extra = {"montant_brut_N", "montant_amort_prov_N", "montant_brut_N1", "montant_amort_prov_N1"}
    net = {**full, "lignes": [{k: v for k, v in r.items() if k not in extra} for r in rows]}
    write("bilan10.json", net)
    # These are checks on explicitly printed nonempty amounts, not imputations.
    def value(cote, label, column):
        matches = [r[column] for r in rows if r["cote"] == cote and r["poste"] == label]
        assert len(matches) == 1 and matches[0] is not None, (cote, label, column)
        return Decimal(matches[0])
    for column in ("montant_net_N", "montant_net_N1"):
        a = value("actif", "TOTAL GENERAL I+II+III", column)
        p = value("passif", "TOTAL GENERAL I+II+III", column)
        assert a == p
        for cote, total2 in (("actif", "TOTAL II (F+G+H+I)"), ("passif", "TOTAL II (F+G+H)")):
            assert value(cote, "TOTAL GENERAL I+II+III", column) == sum(
                value(cote, label, column) for label in ("TOTAL I (A+B+C+D+E)", total2, "TOTAL III"))
    for r in rows:
        if all(r[c] is not None for c in ("montant_brut_N", "montant_amort_prov_N", "montant_net_N")):
            assert Decimal(r["montant_brut_N"]) - Decimal(r["montant_amort_prov_N"]) == Decimal(r["montant_net_N"])
    write("bilan10_provenance.json", {
        "source": "bilan_group_10.pdf",
        "sha256": hashlib.sha256((ROOT / "bilan_group_10.pdf").read_bytes()).hexdigest(),
        "pdf_pages": [1, 2, 3], "printed_pages": [2, 3, 4],
        "method": "Transcription par assistant depuis les pages rendues; aucune sortie de modele consultee.",
        "human_review_status": "A relire par une personne; pas encore une double annotation humaine.",
        "row_count": len(rows),
        "net_numeric_cells": sum(r[c] is not None for r in rows for c in ("montant_net_N", "montant_net_N1")),
        "notes": [
            "Les annees ne sont pas imprimees. La date de depot 29/03/2025 n'est pas un exercice.",
            "Aucune unite explicite sur ces trois pages: inconnue, sans conversion.",
            "Cellules vides conservees null, meme si une somme permettrait d'inferer zero.",
            "Brut et amortissements N-1 absents; tous null. Brut et amortissements au passif absents.",
            "Libelles de marge fusionnee non dupliques. Les lignes de groupe dans la colonne des postes sont incluses une seule fois.",
            "Capital appele et Dont verse sont des informations de decomposition: ne pas les additionner une seconde fois au capital social.",
            "Les rubriques utilisent les libelles de marge; leur correspondance aux sorties est a verifier avant interpretation des scores.",
            "La version Net est destinee a l'evaluation actuelle. La version complete exige l'extension du score aux champs Brut et Amort pour les evaluer."
        ]
    })
    print(f"Created references: {len(rows)} rows; total actif/passif and gross-net checks passed.")
