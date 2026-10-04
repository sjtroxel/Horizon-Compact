"""``hc``: the harness command line. Phase 0.5 has one group, ``smoke``."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import boto3
import botocore
from botocore.exceptions import BotoCoreError, ClientError

import horizon_compact
from horizon_compact.providers.bedrock import REGION, BedrockConverseProvider, make_runtime_client
from horizon_compact.smoke import plan
from horizon_compact.smoke.record import RedactionError
from horizon_compact.smoke.runner import (
    GitInfo,
    SmokeRefusal,
    Versions,
    check_before_calling,
    existing_records,
    record_path,
    run_call,
)

EVIDENCE_RELATIVE = Path("docs/phases/evidence/phase-0.5/smoke")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def default_evidence_dir() -> Path:
    return Path(_git("rev-parse", "--show-toplevel")) / EVIDENCE_RELATIVE


def cmd_list(evidence_dir: Path) -> int:
    records = existing_records(evidence_dir)
    print(f"evidence folder: {EVIDENCE_RELATIVE}")
    for call in plan.PLAN:
        done = "recorded" if record_path(call, evidence_dir, again=False).exists() else "not yet"
        cond = (
            "  (only if Sonnet 5.5 access arrived; needs --confirm-access)"
            if call.conditional
            else ""
        )
        print(f"  {call.number}  {call.name:<28} {call.route.route_kind:<20} {done}{cond}")
    print(f"records so far: {len(records)} of {plan.MAX_RECORDS} (the cap)")
    return 0


def cmd_run(args: argparse.Namespace, evidence_dir: Path) -> int:
    try:
        # Refusals first, from the filesystem alone: nothing touches AWS until the call is allowed.
        check_before_calling(
            args.name, evidence_dir, confirm_access=args.confirm_access, again_reason=args.again
        )
        session = boto3.Session(profile_name=args.profile, region_name=REGION)
        account_id = session.client("sts").get_caller_identity()["Account"]
        provider = BedrockConverseProvider(make_runtime_client(args.profile))
        result = run_call(
            args.name,
            evidence_dir=evidence_dir,
            provider=provider,
            control=session.client("bedrock"),
            account_id=account_id,
            git=GitInfo(sha=_git("rev-parse", "HEAD"), dirty=bool(_git("status", "--porcelain"))),
            versions=Versions(harness=horizon_compact.__version__, botocore=botocore.__version__),
            confirm_access=args.confirm_access,
            again_reason=args.again,
        )
    except SmokeRefusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except RedactionError as exc:
        print(f"NOT WRITTEN, the record could not be made safe: {exc}", file=sys.stderr)
        return 3
    except (BotoCoreError, ClientError) as exc:
        print(f"could not set up the AWS session: {exc}", file=sys.stderr)
        return 2
    rec = result.record
    check = rec["tool_input_check"]
    usage = rec["usage"]
    print(f"call:            {rec['call_name']}")
    print(f"status:          {rec['status']}" + (f"  {rec['error']}" if rec["error"] else ""))
    print(f"stop reason:     {rec['stop_reason']}")
    print(f"tool calls:      {rec['tool_call_count']}")
    print(f"schema problems: {check['problems'] or 'none'}")
    print(f"answer correct:  {check['answer_correct']}")
    print(f"tokens in/out:   {usage['input_tokens']} / {usage['output_tokens']}")
    print(f"est. cost (USD): {rec['est_cost_usd']}")
    print(f"record:          {result.path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hc", description="Horizon Compact harness")
    groups = parser.add_subparsers(dest="group", required=True)
    smoke = groups.add_parser("smoke", help="Phase 0.5 smoke calls")
    smoke.add_argument("--evidence-dir", type=Path, default=None, help=argparse.SUPPRESS)
    actions = smoke.add_subparsers(dest="action", required=True)
    actions.add_parser("list", help="Show the call plan and what exists. No network.")
    run = actions.add_parser("run", help="Make exactly one call. Needs --profile; has no default.")
    run.add_argument("name")
    run.add_argument("--profile", required=True, help="AWS profile; deliberately no default")
    run.add_argument("--confirm-access", action="store_true", help="for the Sonnet 5.5 calls")
    run.add_argument("--again", metavar="REASON", help="make another record of a call that has one")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    evidence_dir: Path = args.evidence_dir or default_evidence_dir()
    if args.action == "list":
        return cmd_list(evidence_dir)
    return cmd_run(args, evidence_dir)


if __name__ == "__main__":
    raise SystemExit(main())
