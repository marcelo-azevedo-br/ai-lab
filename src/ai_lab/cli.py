from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import shutil

from ai_lab.config import FactoryConfig, load_config
from ai_lab.pipeline import PipelineRunner
from ai_lab.run_store import RunStore


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="run_factory.py")
    parser.add_argument("--config", default="config/factory.toml")

    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--deep", action="store_true")

    new_run = subparsers.add_parser("new-run")
    new_run.add_argument("--vertical", required=True)
    new_run.add_argument("--objective", required=True)
    new_run.add_argument("--context", default="")

    run_cmd = subparsers.add_parser("run")
    run_cmd.add_argument("--run-id", required=True)
    run_cmd.add_argument("--through")
    run_cmd.add_argument("--force", action="store_true")
    run_cmd.add_argument("--dry-run", action="store_true")

    approve = subparsers.add_parser("approve")
    approve.add_argument("--run-id", required=True)
    approve.add_argument("--gate", required=True)
    approve.add_argument("--note", default="")

    status = subparsers.add_parser("status")
    status.add_argument("--run-id", required=True)

    return parser


def load_runtime(config_path: str) -> tuple[FactoryConfig, RunStore, PipelineRunner]:
    config = load_config(config_path)
    store = RunStore(config)
    runner = PipelineRunner(config, store)
    return config, store, runner


def cmd_check(config: FactoryConfig, deep: bool) -> int:
    binaries = ["python3", "git", "codex", "ollama"]
    missing = False
    for binary in binaries:
        resolved = shutil.which(binary)
        if resolved:
            print(f"ok     {binary:<8} {resolved}")
        else:
            print(f"missing {binary}")
            missing = True

    paths = [
        config.workspace.runs_dir,
        config.workspace.products_dir,
        config.workspace.prompts_dir,
        config.workspace.agents_dir,
    ]
    for path in paths:
        print(f"path   {path}")

    if deep:
        print("deep-check habilitado: use bootstrap/check.sh para validar modelos locais.")
    return 1 if missing else 0


def cmd_new_run(store: RunStore, *, vertical: str, objective: str, context: str) -> int:
    manifest = store.create_run(vertical=vertical, objective=objective, context=context)
    print(manifest.run_id)
    print(store.write_report(manifest))
    return 0


def cmd_run(runner: PipelineRunner, *, run_id: str, through: str | None, force: bool, dry_run: bool) -> int:
    result = runner.run(run_id, through=through, force=force, dry_run=dry_run)
    print(f"run_id={result.run_id}")
    print(f"executed={','.join(result.executed_steps) or '-'}")
    print(f"status={result.status}")
    if result.stopped_at_gate:
        print(f"waiting_gate={result.stopped_at_gate}")
    return 0


def cmd_approve(store: RunStore, *, run_id: str, gate: str, note: str) -> int:
    manifest = store.load(run_id)
    store.approve(manifest, gate, note)
    print(f"approved {gate} for {run_id}")
    return 0


def cmd_status(store: RunStore, *, run_id: str) -> int:
    manifest = store.load(run_id)
    report = manifest.run_dir(store.config.workspace.runs_dir) / "run-report.md"
    print(report)
    print(report.read_text(encoding="utf-8"))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config, store, runner = load_runtime(args.config)

    if args.command == "check":
        return cmd_check(config, args.deep)
    if args.command == "new-run":
        return cmd_new_run(store, vertical=args.vertical, objective=args.objective, context=args.context)
    if args.command == "run":
        return cmd_run(runner, run_id=args.run_id, through=args.through, force=args.force, dry_run=args.dry_run)
    if args.command == "approve":
        return cmd_approve(store, run_id=args.run_id, gate=args.gate, note=args.note)
    if args.command == "status":
        return cmd_status(store, run_id=args.run_id)

    parser.error(f"Unknown command: {args.command}")
    return 2
