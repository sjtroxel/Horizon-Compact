"""``hc``: the harness command line. ``smoke`` (Phase 0.5) makes single recorded calls; ``sweep`` (Phase 1)
plans, runs, launches, inspects and stops a sweep; ``dossier`` (Phase 2) renders and checks the fictional
company's dossier and calls nothing. Every command that calls a model or authenticates to AWS is typed by
him."""

from __future__ import annotations

import argparse
import os
import random
import signal
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from types import FrameType

import boto3
import botocore
from botocore.exceptions import BotoCoreError, ClientError

import horizon_compact
from horizon_compact.dossier.check import default_repo_root, run_checks
from horizon_compact.dossier.figures import FigureError, load_figures
from horizon_compact.dossier.render import (
    COMPANY_DIR,
    TEMPLATE_PATH,
    TemplateError,
    parse_template,
    render_outputs,
)
from horizon_compact.experiment import Experiment, ExperimentError, load_experiment
from horizon_compact.providers.base import ModelRoute
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
    resolve_profile_arn,
    run_call,
)
from horizon_compact.sweep import launch as sweep_launch
from horizon_compact.sweep import status as sweep_status
from horizon_compact.sweep.identity import IdentityError, RunnerIdentity, identify
from horizon_compact.sweep.plan import (
    SweepPlan,
    SweepRefusal,
    build_plan,
    check_preflight,
    preflight_bound_usd,
    worst_case_per_attempt_usd,
)
from horizon_compact.sweep.prompt import render_prompt
from horizon_compact.sweep.runner import check_official, check_route, run_session
from horizon_compact.sweep.spend import DEVELOPMENT_CAP_USD
from horizon_compact.sweep.store import LocalStore, S3Store, Store

EVIDENCE_RELATIVE = Path("docs/phases/evidence/phase-0.5/smoke")
# "Dirty" means code or docs differ from the commit, not that earlier evidence records are uncommitted.
_CODE_ONLY = ("--", ".", ":(exclude)docs/phases/evidence")


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
            git=GitInfo(
                sha=_git("rev-parse", "HEAD"),
                dirty=bool(_git("status", "--porcelain", *_CODE_ONLY)),
            ),
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


# --- sweep -----------------------------------------------------------------------------------------------

RESULTS_BUCKET_ENV = "HC_RESULTS_BUCKET"
REGION_ENV = "HC_REGION"
PROFILE_ARN_ENV = "HC_SONNET_PROFILE_ARN"
CLEAN_EXIT, REFUSED_EXIT, NOT_CLEAN_EXIT = 0, 2, 3
CHECK_FAILED_EXIT = 1


def _laptop_git() -> tuple[str, bool]:
    return _git("rev-parse", "HEAD"), bool(_git("status", "--porcelain", *_CODE_ONLY))


def _load(args: argparse.Namespace) -> tuple[Experiment, SweepPlan]:
    root = Path(args.experiment_dir) if args.experiment_dir else None
    experiment = load_experiment(args.experiment, root)
    plan_ = build_plan(
        experiment, model_key=args.model, label=args.label, repeats=args.repeats, seed=args.seed
    )
    return experiment, plan_


def _check_cap(args: argparse.Namespace) -> float:
    if args.cap_usd > DEVELOPMENT_CAP_USD and not args.allow_over_cap:
        raise SweepRefusal(
            f"a cap of ${args.cap_usd:.2f} is above the ${DEVELOPMENT_CAP_USD:.0f} development cap; "
            "raising it needs --allow-over-cap, typed by him"
        )
    return float(args.cap_usd)


def _session(args: argparse.Namespace, identity: RunnerIdentity) -> boto3.Session:
    """The laptop must name a profile (deliberately no default); the container uses its task role."""
    if identity.runner == "laptop" and not args.profile:
        raise SweepRefusal("on a laptop, --profile is required and has no default")
    region = os.environ.get(REGION_ENV, REGION)
    return boto3.Session(profile_name=args.profile, region_name=region)


def _route(
    experiment: Experiment, model_key: str, session: boto3.Session, env: dict[str, str]
) -> ModelRoute:
    config = experiment.model(model_key)
    if config.route == "in_region":
        return ModelRoute(model_key, config.model_id, "in_region", invoke_id=config.model_id)
    if config.route == "geo_profile":
        assert config.geo_profile_id is not None
        return ModelRoute(
            model_key, config.model_id, "geo_profile", invoke_id=config.geo_profile_id
        )
    assert config.inference_profile is not None
    # In the container the profile's ARN arrives as an environment variable, since the task role may not list
    # profiles; on the laptop it is found by name, so the account id it contains lives in no file.
    arn = env.get(PROFILE_ARN_ENV) or resolve_profile_arn(
        session.client("bedrock"), config.inference_profile
    )
    return ModelRoute(
        model_key,
        config.model_id,
        "application_profile",
        invoke_id=arn,
        inference_profile=config.inference_profile,
    )


def _store(args: argparse.Namespace, session: boto3.Session) -> Store:
    if args.store == "local":
        return LocalStore(Path(_git("rev-parse", "--show-toplevel")) / "scratch" / "runs")
    bucket = args.bucket or os.environ.get(RESULTS_BUCKET_ENV)
    if not bucket:
        raise SweepRefusal(f"--store s3 needs --bucket or {RESULTS_BUCKET_ENV}")
    return S3Store(session.client("s3"), bucket)


def cmd_sweep_plan(args: argparse.Namespace) -> int:
    experiment, plan_ = _load(args)
    config = experiment.model(plan_.model_key)
    print(f"sweep_id:        {plan_.sweep_id}")
    print(f"content hash:    {plan_.content_hash}")
    print(
        f"runs:            {len(plan_.runs)} ({len(experiment.objectives)} objectives x {plan_.repeats})"
    )
    print(
        f"pacing:          one call start every {60 / (config.requests_per_minute * experiment.models.pace_fraction):.1f}s"
    )
    print(
        f"worst case:      ${worst_case_per_attempt_usd(experiment, plan_):.4f} per attempt, ${preflight_bound_usd(experiment, plan_):.2f} for the sweep (3 attempts per run)"
    )
    objectives = {o.id: o for o in experiment.objectives}
    for n, run in enumerate(plan_.runs, 1):
        print(
            f"  {n:>3}  {run.run_id}  {run.objective_id:<12} repeat {run.repeat}  seed {run.menu_order_seed}"
        )
        if args.show_prompts:
            prompt = render_prompt(experiment, objectives[run.objective_id], run.menu_order_seed)
            if n == 1:
                print("\n--- system (identical on every run) ---\n" + prompt.system)
            print(f"\n--- user, run {n} ---\n{prompt.user}\n")
    return CLEAN_EXIT


def cmd_sweep_run(args: argparse.Namespace) -> int:
    experiment, plan_ = _load(args)
    cap = _check_cap(args)
    identity = identify(os.environ, _laptop_git)
    if args.official:
        check_official(experiment, identity)
    check_route(experiment, plan_.model_key, os.environ)
    check_preflight(experiment, plan_, cap)
    session = _session(args, identity)
    account_id = session.client("sts").get_caller_identity()["Account"]
    route = _route(experiment, plan_.model_key, session, dict(os.environ))
    store = _store(args, session)

    stop_requested = {"flag": False}

    def request_stop(signum: int, frame: FrameType | None) -> None:
        stop_requested["flag"] = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    provider = BedrockConverseProvider(
        make_runtime_client(args.profile, region=session.region_name or REGION),
        region=session.region_name or REGION,
    )
    result = run_session(
        experiment=experiment,
        plan=plan_,
        route=route,
        provider=provider,
        store=store,
        identity=identity,
        account_id=account_id,
        cap_usd=cap,
        max_minutes=args.max_minutes,
        harness_version=horizon_compact.__version__,
        rng=random.Random(),
        should_stop=lambda: stop_requested["flag"],
        progress=lambda line: print(line, file=sys.stderr, flush=True),
    )
    print(f"sweep:           {plan_.sweep_id}")
    print(f"stopped:         {result.stopped}")
    print(
        f"runs finished:   {result.runs_finished_before + result.runs_finished_now} of {result.runs_total}"
    )
    print(f"this session:    {result.attempts_now} attempts, ${result.cost_usd_now:.4f}")
    print(f"sweep total:     ${result.cost_usd_total:.4f} (cap ${cap:.2f})")
    print(f"summary:         {result.summary_key}")
    if result.stopped == "quota_exhausted":
        print("a daily quota is used up: this will not clear by waiting minutes", file=sys.stderr)
    return CLEAN_EXIT if result.clean else NOT_CLEAN_EXIT


def cmd_sweep_launch(args: argparse.Namespace) -> int:
    experiment, plan_ = _load(args)
    cap = _check_cap(args)
    if args.official:
        check_official(experiment, identify({}, _laptop_git))
    check_preflight(experiment, plan_, cap)
    session = _session(args, identify({}, _laptop_git))
    command = [
        "sweep", "run",
        "--experiment", args.experiment,
        "--model", args.model,
        "--repeats", str(args.repeats),
        "--seed", str(args.seed),
        "--label", args.label,
        "--store", "s3",
        "--cap-usd", str(cap),
        "--max-minutes", str(args.max_minutes),
    ]  # fmt: skip
    if args.allow_over_cap:
        command.append("--allow-over-cap")
    arn = sweep_launch.launch_task(
        session.client("ecs"), session.client("ec2"), model_key=args.model, command=command
    )
    print(f"launched:        {arn.rsplit('/', 1)[-1]}")
    print(f"sweep:           {plan_.sweep_id}")
    print(
        "watch it:        hc sweep status (same arguments); stop it: hc sweep stop --model "
        + args.model
    )
    return CLEAN_EXIT


def cmd_sweep_status(args: argparse.Namespace) -> int:
    sweep_id = args.sweep_id or _load(args)[1].sweep_id
    identity = identify({}, _laptop_git)
    summary = sweep_status.summarize(_store(args, _session(args, identity)), sweep_id)
    if summary is None:
        print(f"no manifest for {sweep_id}: nothing has run yet")
        return CLEAN_EXIT
    print(f"sweep:           {summary['sweep_id']}")
    print(
        f"runs finished:   {summary['runs_finished']} of {summary['runs_total']}  {summary['final_statuses']}"
    )
    print(f"attempts:        {summary['attempts']}  {summary['attempt_statuses']}")
    print(f"cost so far:     ${summary['cost_usd']:.4f}")
    for s in summary["sessions"]:
        print(
            f"  session {s['started_at']}  {s['runner']}  stopped: {s['stopped']}  {s['attempts']} attempts"
        )
    return CLEAN_EXIT


def cmd_sweep_stop(args: argparse.Namespace) -> int:
    session = _session(args, identify({}, _laptop_git))
    stopped = sweep_launch.stop_tasks(session.client("ecs"), args.model)
    if not stopped:
        print(f"no running sweep task for {args.model}")
    for arn in stopped:
        print(
            f"stop requested:  {arn.rsplit('/', 1)[-1]} (it stops between attempts and writes its summary)"
        )
    return CLEAN_EXIT


# --- dossier ---------------------------------------------------------------------------------------------


def cmd_dossier_check(root: Path) -> int:
    report = run_checks(root)
    for note in report.notes:
        print(f"note: {note}")
    for failure in report.failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    if report.ok:
        print("dossier check: ok")
    return CLEAN_EXIT if report.ok else CHECK_FAILED_EXIT


def cmd_dossier_render(root: Path) -> int:
    try:
        figures = load_figures(root / COMPANY_DIR)
        template = parse_template((root / TEMPLATE_PATH).read_text(encoding="utf-8"))
        outputs = render_outputs(template, figures)
    except (FigureError, TemplateError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return REFUSED_EXIT
    for relative, content in outputs.items():
        path = root / relative
        unchanged = path.is_file() and path.read_text(encoding="utf-8") == content
        if not unchanged:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
        print(f"{'unchanged' if unchanged else 'wrote':<10} {relative}")
    return CLEAN_EXIT


def cmd_dossier(args: argparse.Namespace) -> int:
    root: Path = args.root or default_repo_root()
    return cmd_dossier_check(root) if args.action == "check" else cmd_dossier_render(root)


def _add_plan_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--experiment", required=True, help="folder under experiment/, e.g. placeholder"
    )
    parser.add_argument("--model", required=True, help="a key in experiment/models.toml")
    parser.add_argument("--repeats", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--experiment-dir", default=None, help=argparse.SUPPRESS)


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile", default=None, help="AWS profile; required on a laptop, no default"
    )
    parser.add_argument("--cap-usd", type=float, default=DEVELOPMENT_CAP_USD)
    parser.add_argument(
        "--allow-over-cap", action="store_true", help="needed to raise the cap above $5"
    )
    parser.add_argument("--max-minutes", type=float, default=30.0)
    parser.add_argument(
        "--official", action="store_true", help="refused until a protocol is committed"
    )


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

    sweep = groups.add_parser("sweep", help="Phase 1 sweeps")
    sweep_actions = sweep.add_subparsers(dest="action", required=True)
    plan_parser = sweep_actions.add_parser(
        "plan", help="Show a sweep's runs and cost bound. Offline."
    )
    _add_plan_arguments(plan_parser)
    plan_parser.add_argument("--show-prompts", action="store_true")
    run_parser = sweep_actions.add_parser("run", help="Run a session here: laptop or container")
    _add_plan_arguments(run_parser)
    _add_run_arguments(run_parser)
    run_parser.add_argument("--store", choices=("local", "s3"), default="local")
    run_parser.add_argument("--bucket", default=None)
    launch_parser = sweep_actions.add_parser("launch", help="Start the sweep as a Fargate task")
    _add_plan_arguments(launch_parser)
    _add_run_arguments(launch_parser)
    status_parser = sweep_actions.add_parser("status", help="Summarize a sweep's stored objects")
    _add_plan_arguments(status_parser)
    status_parser.add_argument("--sweep-id", default=None, help="instead of the plan arguments")
    status_parser.add_argument("--store", choices=("local", "s3"), default="s3")
    status_parser.add_argument("--bucket", default=None)
    status_parser.add_argument("--profile", default=None)
    stop_parser = sweep_actions.add_parser("stop", help="Stop a model's running sweep task")
    stop_parser.add_argument("--model", required=True)
    stop_parser.add_argument("--profile", default=None)

    dossier = groups.add_parser("dossier", help="Phase 2 company dossier. Offline; calls no model.")
    dossier.add_argument("--root", type=Path, default=None, help=argparse.SUPPRESS)
    dossier_actions = dossier.add_subparsers(dest="action", required=True)
    dossier_actions.add_parser(
        "render",
        help="Write the dossier and its public documents from the figures and the template",
    )
    dossier_actions.add_parser(
        "check", help="Check the figures, the template and that every rendered file is fresh"
    )
    return parser


SWEEP_COMMANDS = {
    "plan": cmd_sweep_plan,
    "run": cmd_sweep_run,
    "launch": cmd_sweep_launch,
    "status": cmd_sweep_status,
    "stop": cmd_sweep_stop,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.group == "dossier":
        return cmd_dossier(args)
    if args.group == "sweep":
        try:
            return SWEEP_COMMANDS[args.action](args)
        except (SweepRefusal, ExperimentError, SmokeRefusal) as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return REFUSED_EXIT
        except IdentityError as exc:
            print(f"cannot tell where this is running: {exc}", file=sys.stderr)
            return REFUSED_EXIT
        except (BotoCoreError, ClientError) as exc:
            print(f"AWS error: {exc}", file=sys.stderr)
            return REFUSED_EXIT
    evidence_dir: Path = args.evidence_dir or default_evidence_dir()
    if args.action == "list":
        return cmd_list(evidence_dir)
    return cmd_run(args, evidence_dir)


if __name__ == "__main__":
    raise SystemExit(main())
