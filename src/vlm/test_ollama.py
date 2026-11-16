import argparse
import base64
import json

import pymupdf
import requests

from benchmarking import Bilan, PROMPT, benchmark


def extract(pdf_path, model):
    images = []

    with pymupdf.open(pdf_path) as document:
        for page in document:
            pixmap = page.get_pixmap(dpi=180, alpha=False)

            images.append(
                base64.b64encode(
                    pixmap.tobytes("png")
                ).decode("utf-8")
            )

    schema = Bilan.model_json_schema()

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "stream": False,
            "keep_alive": "10m",
            "format": schema,
            "messages": [{
                "role": "user",
                "content": (
                    PROMPT
                    + "\nSchéma JSON :\n"
                    + json.dumps(schema, ensure_ascii=False)
                ),
                "images": images,
            }],
            "options": {
                "num_ctx": 16384,
                "num_predict": 12000,
            },
        },
        timeout=600,
    )

    response.raise_for_status()
    data = response.json()

    return {
        "raw": data["message"]["content"],
        "input_tokens": data.get("prompt_eval_count"),
        "output_tokens": data.get("eval_count"),
        "usage": {
            "load_duration_ns": data.get("load_duration"),
            "total_duration_ns": data.get("total_duration"),
            "prompt_eval_duration_ns": data.get(
                "prompt_eval_duration"
            ),
            "eval_duration_ns": data.get("eval_duration"),
        },
        "finish": data.get("done_reason"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--model", default="qwen3-vl:4b")
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    benchmark(
        extract_function=extract,
        pdf_path=args.pdf,
        model=args.model,
        output_dir=args.out,
        repeats=args.repeats,
    )