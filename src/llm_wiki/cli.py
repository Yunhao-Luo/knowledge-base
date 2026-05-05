from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import sys

from .assistant import WikiAssistant
from .config import load_config
from .gui import WikiGuiApp
from .providers import ProviderError, build_provider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-wiki")
    parser.add_argument(
        "--config",
        default="config/llm_wiki.toml",
        help="Path to the config file.",
    )
    subparsers = parser.add_subparsers(dest="command")

    ingest = subparsers.add_parser("ingest", help="Ingest a source file.")
    ingest.add_argument("source", nargs="?")
    ingest.add_argument("--all", action="store_true", help="Ingest all pending raw markdown files.")

    query = subparsers.add_parser("query", help="Query the wiki.")
    query.add_argument("question")

    lint = subparsers.add_parser("lint", help="Run a wiki health check.")
    lint.add_argument("--apply", action="store_true", help="Apply fixes suggested by the lint pass.")
    links = subparsers.add_parser("links", help="Inspect or repair internal wiki links.")
    links_subcommands = links.add_subparsers(dest="links_command")
    links_subcommands.add_parser("check", help="List broken or ambiguous internal links.")
    links_subcommands.add_parser("fix", help="Rewrite resolvable internal links to canonical targets.")
    gui = subparsers.add_parser("gui", help="Launch the graphical web interface.")
    gui.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    gui.add_argument("--port", default=8765, type=int, help="Port for the web interface.")
    subparsers.add_parser("status", help="Show current knowledge base status.")
    subparsers.add_parser("repl", help="Start interactive mode.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    if not config_path.exists():
        print(
            f"Missing config file at {config_path}. Copy config/llm_wiki.example.toml first.",
            file=sys.stderr,
        )
        return 1
    try:
        config = load_config(config_path)
    except Exception as exc:  # noqa: BLE001
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    command = args.command or "repl"
    provider = None
    provider_error = None
    if command not in {"status", "gui", "links"}:
        try:
            provider = build_provider(config.provider)
        except ProviderError as exc:
            print(f"Provider error: {exc}", file=sys.stderr)
            return 1
    elif command == "gui":
        try:
            provider = build_provider(config.provider)
        except ProviderError as exc:
            provider_error = str(exc)
    assistant = WikiAssistant(config, provider)

    if command == "ingest":
        if args.all:
            plans = assistant.ingest_pending()
            if not plans:
                print("No pending raw markdown files to ingest.")
            else:
                print_ingest_plans(plans)
        elif args.source:
            plan = assistant.ingest(Path(args.source).resolve())
            print_ingest_plan(plan)
        else:
            print("ingest requires a source path or --all", file=sys.stderr)
            return 1
        return 0
    if command == "query":
        print(assistant.query(args.question))
        return 0
    if command == "lint":
        print_lint_report(assistant.lint(apply=args.apply), applied=args.apply)
        return 0
    if command == "links":
        if args.links_command == "fix":
            changed, findings = assistant.fix_links()
            print_link_fix_result(changed, findings)
            return 0
        print_link_findings(assistant.check_links())
        return 0
    if command == "status":
        print(assistant.status())
        return 0
    if command == "gui":
        app = WikiGuiApp(assistant, provider_available=provider is not None, provider_error=provider_error)
        server = app.create_server(args.host, args.port)
        url = f"http://{args.host}:{args.port}"
        print(f"LLM Wiki GUI running at {url}")
        if provider_error:
            print(f"Provider warning: {provider_error}")
            print("Browsing works, but assistant actions will stay disabled until the provider is configured.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping GUI.")
        finally:
            server.server_close()
        return 0
    return repl(assistant)


def repl(assistant: WikiAssistant) -> int:
    print("LLM Wiki REPL. Type 'help' for commands and 'exit' to quit.")
    while True:
        try:
            raw = input("wiki> ").strip()
        except EOFError:
            print()
            return 0
        if not raw:
            continue
        if raw in {"exit", "quit"}:
            return 0
        if raw == "help":
            print(
                "Commands: status | ingest <path> | ingest --all | query <question> | "
                "lint [--apply] | links check | links fix | gui | exit"
            )
            continue
        try:
            parts = shlex.split(raw)
        except ValueError as exc:
            print(f"Parse error: {exc}")
            continue
        cmd, *rest = parts
        try:
            if cmd == "status":
                print(assistant.status())
            elif cmd == "ingest" and rest:
                if rest == ["--all"] or rest == ["all"]:
                    plans = assistant.ingest_pending()
                    if not plans:
                        print("No pending raw markdown files to ingest.")
                    else:
                        print_ingest_plans(plans)
                else:
                    plan = assistant.ingest(Path(rest[0]).expanduser().resolve())
                    print_ingest_plan(plan)
            elif cmd == "query" and rest:
                print(assistant.query(" ".join(rest)))
            elif cmd == "lint":
                print_lint_report(assistant.lint(apply="--apply" in rest), applied="--apply" in rest)
            elif cmd == "links":
                if rest and rest[0] == "fix":
                    changed, findings = assistant.fix_links()
                    print_link_fix_result(changed, findings)
                else:
                    print_link_findings(assistant.check_links())
            elif cmd == "gui":
                print("Launch the GUI from the shell with `./wiki gui`.")
            else:
                print("Unknown command. Type 'help' for usage.")
        except Exception as exc:  # noqa: BLE001
            print(f"Error: {exc}")


def print_ingest_plan(plan) -> None:
    print(f"Ingested into {plan.source_summary_path}")
    for update in plan.wiki_updates:
        print(f"Updated {update.path}")
    if plan.assistant_notes:
        print()
        print(plan.assistant_notes)


def print_ingest_plans(plans) -> None:
    print(f"Processed {len(plans)} source(s).")
    for plan in plans:
        print()
        print_ingest_plan(plan)


def print_lint_report(report, applied: bool) -> None:
    print(report.summary)
    for finding in report.findings:
        print(f"- {finding}")
    if applied and report.wiki_updates:
        print()
        print("Applied updates:")
        for update in report.wiki_updates:
            print(f"- {update.path}")
    if report.suggested_pages:
        print()
        print("Suggested pages:")
        for page in report.suggested_pages:
            print(f"- {page}")
    if report.assistant_notes:
        print()
        print(report.assistant_notes)


def print_link_findings(findings) -> None:
    if not findings:
        print("No broken or ambiguous internal wiki links found.")
        return
    print(f"Found {len(findings)} internal link issue(s).")
    for finding in findings:
        summary = f"- {finding.reason}: {finding.source_path} -> {finding.target}"
        if finding.suggestion:
            summary += f" (suggested: {finding.suggestion})"
        print(summary)


def print_link_fix_result(changed, findings) -> None:
    if changed:
        print(f"Rewrote internal links in {len(changed)} file(s).")
        for path in changed:
            print(f"- {path}")
    else:
        print("No automatic link rewrites were needed.")
    print()
    print_link_findings(findings)


if __name__ == "__main__":
    raise SystemExit(main())
