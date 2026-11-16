import argparse
import base64

from dotenv import load_dotenv
from openai import OpenAI

from benchmarking import Bilan, Ligne, PROMPT, benchmark


class LigneGPT(Ligne):
    montant_brut_N: str | None
    montant_amort_prov_N: str | None
    montant_brut_N1: str | None
    montant_amort_prov_N1: str | None


class BilanGPT(Bilan):
    lignes: list[LigneGPT]


GPT_PROMPT = PROMPT.replace(
    "- Extrais uniquement les montants NET de N et N-1.",
    "- Extrais les colonnes BRUT, AMORTISSEMENTS/PROVISIONS et NET de N et N-1."
) + """
Champs supplementaires par ligne :
- montant_brut_N et montant_brut_N1 : colonnes BRUT imprimees.
- montant_amort_prov_N et montant_amort_prov_N1 : colonnes AMORT./PROV. imprimees.
- montant_net_N et montant_net_N1 : colonnes NET imprimees.
Associe chaque colonne a son exercice selon les en-tetes du document.
Si BRUT ou AMORT./PROV. n'existe pas pour un exercice, retourne null.
Au PASSIF, conserve les montants des exercices dans les champs NET;
BRUT et AMORT./PROV. restent null sauf colonnes explicitement presentes.
Ne deduis jamais BRUT ou AMORT./PROV. a partir du NET, ni l'inverse.
"""


load_dotenv()


def extract(pdf_path, model):
    client = OpenAI(timeout=300, max_retries=0)

    encoded_pdf = base64.b64encode(
        pdf_path.read_bytes()
    ).decode("utf-8")

    response = client.responses.parse(
        model=model,
        input=[{
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": GPT_PROMPT,
                },
                {
                    "type": "input_file",
                    "filename": pdf_path.name,
                    "file_data": (
                        "data:application/pdf;base64,"
                        + encoded_pdf
                    ),
                },
            ],
        }],
        text_format=BilanGPT,
        max_output_tokens=12000,
    )

    usage = response.usage

    return {
        "raw": response.output_text,
        "input_tokens": usage.input_tokens if usage else None,
        "output_tokens": usage.output_tokens if usage else None,
        "usage": usage.model_dump() if usage else {},
        "finish": response.status,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--input-rate", type=float)
    parser.add_argument("--output-rate", type=float)
    args = parser.parse_args()

    benchmark(
        extract_function=extract,
        pdf_path=args.pdf,
        model=args.model,
        output_dir=args.out,
        repeats=args.repeats,
        input_rate=args.input_rate,
        output_rate=args.output_rate,
        output_schema=BilanGPT,
    )
