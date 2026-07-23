"""CLI entry point for Script Splitter."""
import argparse
from pathlib import Path
from script_splitter.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="script-splitter", description="Hybrid screenplay parser: layout clarifier + rule extraction + LLM semantic routing.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    p = subparsers.add_parser("parse", help="Parse a screenplay file.")
    p.add_argument("script_path", help="Path to screenplay (PDF, DOCX, TXT, Fountain)")
    p.add_argument("--output", "-o", default="Script_Splitter_Output", help="Output directory")
    p.add_argument("--stage", type=int, default=3, choices=[1, 2, 3], help="Pipeline stage (1=scenes, 2=+entities, 3=+LLM)")
    p.add_argument("--no-llm", action="store_true", default=False, help="Skip all LLM calls")
    p.add_argument("--no-nlp", action="store_true", default=False, help="Skip spaCy NLP pre-scan")
    p.add_argument("--quiet", action="store_true", default=False, help="Suppress progress output")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "parse":
        progress = None if args.quiet else _print_progress
        progress(f"[start] Parsing {args.script_path} stage={args.stage} (llm={'off' if args.no_llm else 'on'})")
        try:
            result = run_pipeline(
                Path(args.script_path),
                stage=args.stage,
                use_llm=not args.no_llm,
                use_nlp=not args.no_nlp,
                output_dir=args.output,
                progress=progress,
                llm_cache_dir=Path(args.output) / "llm_cache" if args.stage >= 3 and not args.no_llm else None,
            )
        except KeyboardInterrupt:
            print("\nStopped by user.", flush=True)
            return 130
        r = result.report
        print(f"Parsed {r.heading_count} headings into {r.scene_count} scenes ({r.shot_count} shots) at {args.output}")
        print(f"Characters: {r.character_count}, Locations: {r.location_asset_count}, Visual elements: {r.visual_element_count}")
    return 0


def _print_progress(message: str) -> None:
    print(message, flush=True)


if __name__ == "__main__":
    raise SystemExit(main())

