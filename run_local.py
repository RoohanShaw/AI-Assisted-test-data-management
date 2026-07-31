"""
run_local.py — Standalone script to run the full pipeline locally.

Flow:
  SampleInput.json -> JSON Parser -> Extract Fields -> Semantic Classification
  (Cache -> FAISS -> Heuristic) -> Business Rules -> Faker/Custom Generator
  -> Fill Iterations -> Build Output JSON -> Write SampleOutput.json

Usage:
  python run_local.py                              # uses SampleInput.json
  python run_local.py --input my_input.json        # custom input
  python run_local.py --excel TP_AppointmentList_TDM.xlsx   # from Excel
  python run_local.py --module Appointment         # hint for classification
"""

import argparse
import io
import json
import logging
import sys
from pathlib import Path

# ── Logging (UTF-8 safe for Windows) ─────────────────────────────────────────
_handler = logging.StreamHandler(
    io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stdout, "buffer") else sys.stdout
)
_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[_handler])
logger = logging.getLogger("run_local")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
INPUT_JSON  = BASE_DIR / "SampleInput.json"
OUTPUT_JSON = BASE_DIR / "SampleOutput.json"
EXCEL_FILE  = BASE_DIR / "TP_AppointmentList_TDM.xlsx"


def main():
    parser = argparse.ArgumentParser(
        description="AI Test Data Generator -- local pipeline runner"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=str(INPUT_JSON),
        help=f"Path to input JSON file (default: {INPUT_JSON.name})"
    )
    parser.add_argument(
        "--excel", "-e",
        type=str,
        default=None,
        help="Path to Excel TDM file. If provided, overrides --input."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=str(OUTPUT_JSON),
        help=f"Path to write output JSON (default: {OUTPUT_JSON.name})"
    )
    parser.add_argument(
        "--module", "-m",
        type=str,
        default="Appointment",
        help="Business module hint for classification (default: Appointment)"
    )
    parser.add_argument(
        "--locale", "-l",
        type=str,
        default="en_IN",
        help="Faker locale (default: en_IN)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducible output"
    )
    args = parser.parse_args()

    # ── Step 1: Warm up embedding model + FAISS ───────────────────────────────
    logger.info("=" * 60)
    logger.info("  AI Test Data Generator -- Local Pipeline")
    logger.info("  Classification: Cache -> FAISS -> Heuristic (no external API)")
    logger.info("=" * 60)

    logger.info("Step 1/4 -- Loading embedding model (SentenceTransformer) ...")
    from app.embedding_engine import warm_up
    warm_up()

    logger.info("Step 2/4 -- Initialising FAISS knowledge base ...")
    from app.faiss_store import get_store
    store = get_store()
    store.initialize()
    logger.info(f"  FAISS ready: {store.size} vectors indexed.")

    # ── Step 2: Parse input ───────────────────────────────────────────────────
    logger.info("Step 3/4 -- Parsing input ...")
    from app.excel_parser import parse_json_input, parse_excel_input

    if args.excel:
        excel_path = Path(args.excel)
        logger.info(f"  Source: Excel -> {excel_path.name}")
        normalized = parse_excel_input(excel_path)
    else:
        input_path = Path(args.input)
        logger.info(f"  Source: JSON  -> {input_path.name}")
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        normalized = parse_json_input(data)

    suite_count = len(normalized.get("test_suites", {}))
    logger.info(
        f"  Package: '{normalized['test_package_name']}' | "
        f"Test Suites found: {suite_count}"
    )
    for suite_name, suite_data in normalized["test_suites"].items():
        obj_names = list(suite_data.get("objects", {}).keys())
        for oname in obj_names:
            odata = suite_data["objects"][oname]
            logger.info(
                f"    [{suite_name}] {oname[:60]} | "
                f"iterations={odata['iteration_count']} | "
                f"fields={len(odata['fields'])}"
            )

    # ── Step 3: Run the full pipeline ─────────────────────────────────────────
    logger.info("Step 4/4 -- Running classification + generation pipeline ...")
    logger.info(f"  Module: '{args.module}' | Locale: '{args.locale}' | Seed: {args.seed}")

    from app.pipeline import run_pipeline
    result = run_pipeline(
        normalized=normalized,
        module=args.module,
        locale=args.locale,
        seed=args.seed,
    )

    output   = result["output"]
    metadata = result["metadata"]
    warnings = result["warnings"]

    # ── Step 4: Write output ──────────────────────────────────────────────────
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info(f"  Output written -> {output_path}")
    logger.info(f"  Test Suites generated: {list(output.get('TestSuites', {}).keys())}")
    logger.info(f"  Warnings: {len(warnings)}")
    logger.info("=" * 60)

    # Print field classification summary
    if metadata:
        logger.info("\nField Classification Summary:")
        logger.info(f"  {'Field':<45} {'Category':<30} {'Source':<10} {'Conf.'}")
        logger.info(f"  {'-'*45} {'-'*30} {'-'*10} {'-'*6}")
        for fname, meta in metadata.items():
            logger.info(
                f"  {fname:<45} {meta['category']:<30} {meta['source']:<10} "
                f"{meta['confidence']:.2f}"
            )

    if warnings:
        logger.warning(f"\n{len(warnings)} classification warning(s):")
        for w in warnings:
            logger.warning(f"  [!] {w}")

    logger.info("\nDone!")
    return output


if __name__ == "__main__":
    main()
