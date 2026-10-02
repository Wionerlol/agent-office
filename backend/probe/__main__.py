"""Explicit diagnostic commands; no startup hooks or frontend protocol changes."""

import argparse
import asyncio
import sys
from pathlib import Path

from backend.probe.observe import observe_thread
from backend.probe.record import ProbeRecorder, private_output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture", help="Sanitize an explicitly selected JSONL stream")
    capture.add_argument(
        "--source",
        required=True,
        choices=[
            "codex-exec",
            "codex-app-server",
            "codex-rollout",
            "office-wrapper",
            "tool-process",
        ],
    )
    capture.add_argument("--input", type=Path, help="Explicit file; default is stdin")
    observe = commands.add_parser(
        "observe", help="Attach to one loaded native thread, without replies"
    )
    observe.add_argument("--socket", type=Path, required=True, help="Local app-server Unix socket")
    observe.add_argument("--thread", required=True, help="Native thread ID, not an office Agent ID")
    observe.add_argument("--duration", type=float, default=60)
    experiment = commands.add_parser("experiment", help="Run controlled real Codex scenarios A–E")
    experiment.add_argument("--codex", default="codex")
    experiment.add_argument("--scenarios", nargs="+", choices=list("ABCDE"), default=list("ABCDE"))
    experiment.add_argument(
        "--output-dir", type=Path, required=True, help="Use runtime/probe/run-N"
    )
    for command in (capture, observe):
        command.add_argument("--workspace", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True, help="Use runtime/probe/*.jsonl")
    args = parser.parse_args(argv)
    try:
        if args.command == "experiment":
            from backend.probe.experiments import run_experiments

            asyncio.run(run_experiments(args.output_dir, args.codex, args.scenarios))
            return
        if args.command == "observe" and not 0 < args.duration <= 3600:
            parser.error("duration must be between 0 and 3600 seconds")
        with private_output(args.output) as output:
            source = args.source if args.command == "capture" else "codex-app-server"
            recorder = ProbeRecorder(output, source, args.workspace)
            if args.command == "observe":
                asyncio.run(
                    observe_thread(
                        args.socket,
                        args.thread,
                        args.workspace,
                        recorder,
                        args.duration,
                    )
                )
            else:
                stream = args.input.open(encoding="utf-8") if args.input else sys.stdin
                try:
                    for line in stream:
                        recorder.line(line)
                finally:
                    if args.input:
                        stream.close()
    except Exception as error:
        # Exception strings can contain server content or paths; log only the class.
        parser.exit(2, f"Probe unavailable: {type(error).__name__}\n")
    except KeyboardInterrupt:
        parser.exit(130, "Probe stopped\n")


if __name__ == "__main__":
    main()
