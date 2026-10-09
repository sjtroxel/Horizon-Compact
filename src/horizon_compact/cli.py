"""``hc``: the harness command line. ``smoke`` (Phase 0.5) makes single recorded calls; ``sweep`` (Phase 1)
plans, runs, launches, inspects and stops a sweep; ``dossier`` (Phase 2) renders and checks the fictional
company's dossier and calls nothing; ``scenarios`` (Phase 2.5) renders and checks the four scenarios and
calls nothing. Every command that calls a model or authenticates to AWS is typed by him."""

from __future__ import annotations

import argparse
import os
import random
import signal
import subprocess
import sys
from collections.abc import Callable, Sequence
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
from horizon_compact.probes.questions import ProbeError
from horizon_compact.probes.run import (
    ProbeSet,
    check_probe_model,
    load_probe_sets,
    probe_estimate,
    probe_report,
    probe_run_id,
    run_probes,
)
from horizon_compact.protocol.gate import check_official, refusal_message, run_gate
from horizon_compact.protocol.lock import (
    EXPERIMENT as LOCK_EXPERIMENT,
)
from horizon_compact.protocol.lock import (
    LOCK_RELATIVE,
    LockError,
    check_lock,
    render_lock,
    write_lock,
)
from horizon_compact.providers.base import ModelRoute, Provider
from horizon_compact.providers.bedrock import REGION, BedrockConverseProvider, make_runtime_client
from horizon_compact.providers.ollama import DEFAULT_URL, OllamaProvider
from horizon_compact.providers.openrouter import OpenRouterKeyError, OpenRouterProvider, read_key
from horizon_compact.scenarios.check import run_checks as scenarios_run_checks
from horizon_compact.scenarios.render import (
    ScenarioSourceError,
    load_scenario_figures,
    render_all,
)
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
from horizon_compact.sweep.blind import failures_view, format_report
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
from horizon_compact.sweep.runner import check_route, run_session
from horizon_compact.sweep.spend import DEVELOPMENT_CAP_USD
from horizon_compact.sweep.store import LocalStore, S3Store, Store
from horizon_compact.sweep.warning import SpendEstimate, format_warning, sweep_estimate

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
OLLAMA_URL_ENV = "HC_OLLAMA_URL"
# A local run has no AWS account. The record writer wants one id to redact, so it gets one that is plainly
# not real.
LOCAL_ACCOUNT_ID = "000000000000"
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
        experiment,
        model_key=args.model,
        label=args.label,
        repeats=args.repeats,
        seed=args.seed,
        scenarios=args.scenario or None,
        templates=args.template or None,
        official=getattr(args, "official", False),
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


def _store(args: argparse.Namespace, session: boto3.Session | None) -> Store:
    if args.store == "local":
        return LocalStore(Path(_git("rev-parse", "--show-toplevel")) / "scratch" / "runs")
    bucket = args.bucket or os.environ.get(RESULTS_BUCKET_ENV)
    if not bucket:
        raise SweepRefusal(f"--store s3 needs --bucket or {RESULTS_BUCKET_ENV}")
    assert session is not None  # an s3 store always comes with a session
    return S3Store(session.client("s3"), bucket)


def _check_local(args: argparse.Namespace, identity: RunnerIdentity) -> None:
    """A local model runs on this laptop, keeps its records here, and never touches AWS."""
    if identity.runner != "laptop":
        raise SweepRefusal("a local model runs on the laptop only: the container cannot reach it")
    if args.store != "local":
        raise SweepRefusal("a local model's runs stay on this laptop: use --store local")


def _check_openrouter(args: argparse.Namespace, identity: RunnerIdentity) -> None:
    """An OpenRouter model runs on this laptop, with a key typed here, and keeps its records here."""
    if identity.runner != "laptop":
        raise SweepRefusal("an OpenRouter model runs on the laptop only: the container has no key")
    if args.store != "local":
        raise SweepRefusal("an OpenRouter model's runs stay on this laptop: use --store local")


def _confirm_spend(
    estimate: Callable[[Store], SpendEstimate], model_key: str, cap_usd: float, store: Store
) -> None:
    """Print what the run is expected to cost and ask. Anything but ``y`` (or no answer at all) is a refusal,
    so nothing is sent and no key is asked for."""
    print(format_warning(model_key, estimate(store), cap_usd))
    try:
        answer = input("Continue? [y/N] ")
    except EOFError:
        answer = ""
    if answer.strip().lower() != "y":
        raise SweepRefusal("not confirmed: nothing was sent")


def _connect(
    args: argparse.Namespace,
    experiment: Experiment,
    model_key: str,
    identity: RunnerIdentity,
    estimate: Callable[[Store], SpendEstimate],
    cap_usd: float,
) -> tuple[Provider, ModelRoute, Store, str]:
    """The provider, route, store and account id for a run on this machine: a sweep or a probe run. A local or
    OpenRouter model touches no AWS; a Bedrock model needs a session."""
    config = experiment.model(model_key)
    provider: Provider
    if config.route == "openrouter":
        # No AWS session either. The spend warning comes after every refusal and before the key, and the key
        # is asked for last, so a refused run never prompts; it lives in the provider and nowhere else.
        _check_openrouter(args, identity)
        route = ModelRoute(model_key, config.model_id, "openrouter", invoke_id=config.model_id)
        store = _store(args, None)
        _confirm_spend(estimate, model_key, cap_usd, store)
        try:
            provider = OpenRouterProvider(read_key(os.environ))
        except OpenRouterKeyError as exc:
            raise SweepRefusal(str(exc)) from exc
        return provider, route, store, LOCAL_ACCOUNT_ID
    if config.route == "local":
        # Nothing on this path creates an AWS session, calls STS or reads a profile.
        _check_local(args, identity)
        assert config.num_ctx is not None  # a local route always has one (ModelConfig checks)
        route = ModelRoute(model_key, config.model_id, "local", invoke_id=config.model_id)
        provider = OllamaProvider(os.environ.get(OLLAMA_URL_ENV, DEFAULT_URL), config.num_ctx)
        return provider, route, _store(args, None), LOCAL_ACCOUNT_ID
    session = _session(args, identity)
    account_id = session.client("sts").get_caller_identity()["Account"]
    route = _route(experiment, model_key, session, dict(os.environ))
    provider = BedrockConverseProvider(
        make_runtime_client(args.profile, region=session.region_name or REGION),
        region=session.region_name or REGION,
    )
    return provider, route, _store(args, session), account_id


def cmd_sweep_plan(args: argparse.Namespace) -> int:
    experiment, plan_ = _load(args)
    config = experiment.model(plan_.model_key)
    print(f"sweep_id:        {plan_.sweep_id}")
    print(f"content hash:    {plan_.content_hash}")
    print(
        f"runs:            {len(plan_.runs)} ({len(plan_.scenarios)} scenarios x "
        f"{len(experiment.objectives)} objectives x {len(plan_.templates)} templates x "
        f"{plan_.repeats} repeats)"
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
            f"  {n:>3}  {run.run_id}  {run.scenario_id:<8} {run.objective_id:<12} {run.wording_id} "
            f"repeat {run.repeat}  seed {run.menu_order_seed}"
        )
        if args.show_prompts:
            prompt = render_prompt(
                experiment,
                experiment.get_scenario(run.scenario_id),
                objectives[run.objective_id],
                run.wording_id,
                run.menu_order_seed,
            )
            if n == 1:
                print("\n--- system (identical on every run) ---\n" + prompt.system)
            print(f"\n--- user, run {n} ---\n{prompt.user}\n")
    return CLEAN_EXIT


def cmd_sweep_dry_run(args: argparse.Namespace) -> int:
    """Every gate check, the plan, and nothing else: no write, no provider, no AWS (section 7.2)."""
    if not args.official:
        raise SweepRefusal("--dry-run checks an official sweep against the lock: add --official")
    experiment, plan_ = _load(args)
    result = run_gate(experiment, plan_, identify(os.environ, _laptop_git), require_container=False)
    print(f"sweep:   {plan_.sweep_id} ({len(plan_.runs)} runs, model {plan_.model_key})")
    for note in result.notes:
        print(f"note: {note}")
    if not result.ok:
        print(refusal_message(result), file=sys.stderr)
        return REFUSED_EXIT
    print("official sweep: every check passes (dry run; nothing written, nothing called)")
    return CLEAN_EXIT


def cmd_sweep_run(args: argparse.Namespace) -> int:
    if args.dry_run:
        return cmd_sweep_dry_run(args)
    experiment, plan_ = _load(args)
    cap = _check_cap(args)
    identity = identify(os.environ, _laptop_git)
    if args.official:
        check_official(experiment, plan_, identity)
    check_route(experiment, plan_.model_key, os.environ)
    check_preflight(experiment, plan_, cap)
    provider, route, store, account_id = _connect(
        args,
        experiment,
        plan_.model_key,
        identity,
        lambda store: sweep_estimate(experiment, plan_, store),
        cap,
    )

    stop_requested = {"flag": False}

    def request_stop(signum: int, frame: FrameType | None) -> None:
        stop_requested["flag"] = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

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
    launch_route = experiment.model(plan_.model_key).route
    if launch_route == "local":
        raise SweepRefusal(
            f"{plan_.model_key} is a local model: it runs on this laptop, so use `hc sweep run`"
        )
    if launch_route == "openrouter":
        raise SweepRefusal(
            f"{plan_.model_key} is an OpenRouter model: it runs on this laptop with a key typed "
            "here, so use `hc sweep run`"
        )
    cap = _check_cap(args)
    if args.official:
        # The laptop checks 1-7 before anything starts; the task checks all eight again in the container.
        preflight = run_gate(
            experiment, plan_, identify({}, _laptop_git), require_container=False, why="launch"
        )
        if not preflight.ok:
            raise SweepRefusal(refusal_message(preflight))
        raise SweepRefusal(
            "an official launch is not wired yet: forwarding --official to the task is Phase 4's run-code "
            "item (KNOWN-GAPS). Gate checks 1-7 pass on this laptop."
        )
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
    for scenario_id in args.scenario or []:
        command += ["--scenario", scenario_id]
    for template_id in args.template or []:
        command += ["--template", template_id]
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
    session = None if args.store == "local" else _session(args, identity)
    summary = sweep_status.summarize(_store(args, session), args.experiment, sweep_id)
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


FORMAT_REPORT_DIR = "docs/phases/evidence/phase-2.5/format"


def cmd_sweep_report(args: argparse.Namespace) -> int:
    """The blind format report and the failures view (Phase 2.5 IMPLEMENTATION doc section 11.3): the only
    readers of a company run's records. Offline for a local store."""
    experiment, plan_ = _load(args)
    session = None if args.store == "local" else _session(args, identify({}, _laptop_git))
    store = _store(args, session)
    top = Path(_git("rev-parse", "--show-toplevel"))
    folder = top / FORMAT_REPORT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    for name, text in (
        (f"{plan_.sweep_id}.md", format_report(store, experiment, plan_)),
        (f"{plan_.sweep_id}-failures.md", failures_view(store, experiment, plan_)),
    ):
        path = folder / name
        path.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(top)}")
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


# --- protocol (Phase 3.5 step 4) -------------------------------------------------------------------------


def cmd_protocol_check(root: Path) -> int:
    report = check_lock(root)
    for failure in report.failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    for note in report.notes:
        print(f"note: {note}", file=sys.stderr if report.failures else sys.stdout)
    if report.ok:
        print("protocol check: ok")
    return CLEAN_EXIT if report.ok else CHECK_FAILED_EXIT


def cmd_protocol_lock(root: Path, models: list[str], experiment: str, write: bool) -> int:
    try:
        if write:
            write_lock(root, models, experiment=experiment)
            print(f"wrote {LOCK_RELATIVE}")
        else:
            print(render_lock(root, models, experiment=experiment), end="")
    except LockError as exc:
        for reason in exc.reasons:
            print(f"refused: {reason}", file=sys.stderr)
        return REFUSED_EXIT
    return CLEAN_EXIT


def cmd_protocol(args: argparse.Namespace) -> int:
    root: Path = args.root or default_repo_root()
    if args.action == "check":
        return cmd_protocol_check(root)
    return cmd_protocol_lock(root, args.models, args.experiment, args.write)


# --- probes ----------------------------------------------------------------------------------------------

PROBE_REPORT_DIR = "docs/phases/evidence/phase-2.5/probes"


def _probe_sets(args: argparse.Namespace) -> tuple[Experiment, list[ProbeSet]]:
    root = Path(args.experiment_dir) if args.experiment_dir else None
    experiment = load_experiment(args.experiment, root)
    check_probe_model(experiment, args.model)  # before anything else is read or asked
    if args.repeats < 1:
        raise SweepRefusal("repeats must be at least 1")
    figures = load_scenario_figures(experiment.root.parent)
    return experiment, load_probe_sets(experiment, figures, args.scenario or None)


def cmd_probes_run(args: argparse.Namespace) -> int:
    experiment, sets = _probe_sets(args)
    cap = _check_cap(args)
    identity = identify(os.environ, _laptop_git)
    provider, route, store, account_id = _connect(
        args,
        experiment,
        args.model,
        identity,
        lambda store: probe_estimate(experiment, args.model, args.label, args.repeats, sets, store),
        cap,
    )
    stop_requested = {"flag": False}

    def request_stop(signum: int, frame: FrameType | None) -> None:
        stop_requested["flag"] = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    result = run_probes(
        experiment=experiment,
        model_key=args.model,
        sets=sets,
        repeats=args.repeats,
        label=args.label,
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
    print(f"probe run:       {result.run_id}")
    print(f"stopped:         {result.stopped}")
    print(
        f"repeats done:    {result.repeats_done_before + result.repeats_done_now} of {result.repeats_total}"
    )
    print(f"this session:    {result.calls_now} calls, ${result.cost_usd_now:.4f}")
    print("report:          hc probes report (same arguments) writes it under " + PROBE_REPORT_DIR)
    return CLEAN_EXIT if result.clean else NOT_CLEAN_EXIT


def cmd_probes_report(args: argparse.Namespace) -> int:
    experiment, sets = _probe_sets(args)
    run_id = probe_run_id(experiment, args.model, args.label, args.repeats, sets)
    top = Path(_git("rev-parse", "--show-toplevel"))
    store = LocalStore(top / "scratch" / "runs")
    report = probe_report(store, experiment, run_id, sets, args.repeats)
    path = top / PROBE_REPORT_DIR / f"{run_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {path.relative_to(top)}")
    return CLEAN_EXIT


PROBE_COMMANDS = {"run": cmd_probes_run, "report": cmd_probes_report}


# --- scenarios -------------------------------------------------------------------------------------------


def cmd_scenarios_check(root: Path) -> int:
    report = scenarios_run_checks(root)
    for note in report.notes:
        print(f"note: {note}")
    for failure in report.failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    if report.ok:
        print("scenarios check: ok")
    return CLEAN_EXIT if report.ok else CHECK_FAILED_EXIT


def cmd_scenarios_render(root: Path) -> int:
    try:
        outputs = render_all(root)
    except (FigureError, ScenarioSourceError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return REFUSED_EXIT
    for relative, content in outputs.files.items():
        path = root / relative
        unchanged = path.is_file() and path.read_text(encoding="utf-8") == content
        if not unchanged:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
        print(f"{'unchanged' if unchanged else 'wrote':<10} {relative}")
    return CLEAN_EXIT


def cmd_scenarios(args: argparse.Namespace) -> int:
    root: Path = args.root or default_repo_root()
    return cmd_scenarios_check(root) if args.action == "check" else cmd_scenarios_render(root)


# --- simulate (Phase 3 step 10) ---------------------------------------------------------------------------

SIMULATION_EVIDENCE = Path("docs/phases/evidence/phase-3")
SIMULATION_QUICK = Path("scratch/simulation-quick")


def cmd_simulate(args: argparse.Namespace) -> int:
    """The simulations need the analysis group (numpy, scipy, statsmodels), which the container image leaves
    out, so they are imported here and never at the top of this module."""
    from horizon_compact.simulation import report, runner

    root: Path = args.root or default_repo_root()
    if args.action == "run":
        plan = runner.QUICK if args.quick else runner.FULL
        folder = root / (SIMULATION_QUICK if args.quick else SIMULATION_EVIDENCE)
        runner.run(plan, folder / report.RESULTS_NAME, root=root, workers=args.workers)
        return CLEAN_EXIT
    folder = root / (SIMULATION_QUICK if args.quick else SIMULATION_EVIDENCE)
    for path in report.write_reports(folder):
        print(f"wrote {path}")
    return CLEAN_EXIT


def _add_plan_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--experiment", required=True, help="folder under experiment/, e.g. placeholder"
    )
    parser.add_argument("--model", required=True, help="a key in experiment/models.toml")
    parser.add_argument("--repeats", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument(
        "--scenario",
        action="append",
        default=None,
        help="a scenario id; repeat the flag for several; default: every scenario",
    )
    parser.add_argument(
        "--template",
        action="append",
        default=None,
        help="a wording template id (w1-w3); repeat for several; default: every template",
    )
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
        "--official", action="store_true", help="checked against experiment/protocol/prereg.lock"
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
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="with --official: run every gate check and plan the sweep; write nothing, call nothing",
    )
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
    report_parser = sweep_actions.add_parser(
        "report",
        help="Write the blind format report and the failures view. No amounts, choices or memos.",
    )
    _add_plan_arguments(report_parser)
    report_parser.add_argument("--store", choices=("local", "s3"), default="local")
    report_parser.add_argument("--bucket", default=None)
    report_parser.add_argument("--profile", default=None)
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

    probes = groups.add_parser(
        "probes", help="Phase 2.5 comprehension probes. Development models only; no objective."
    )
    probe_actions = probes.add_subparsers(dest="action", required=True)
    for name, text in (
        ("run", "Ask each scenario's questions; one call per repeat"),
        ("report", "Write the report from the stored records. Offline."),
    ):
        probe_parser = probe_actions.add_parser(name, help=text)
        probe_parser.add_argument("--experiment", required=True)
        probe_parser.add_argument("--model", required=True, help="a development model")
        probe_parser.add_argument("--repeats", type=int, default=5)
        probe_parser.add_argument("--label", required=True)
        probe_parser.add_argument(
            "--scenario", action="append", default=None, help="repeat for several; default all"
        )
        probe_parser.add_argument("--experiment-dir", default=None, help=argparse.SUPPRESS)
        if name == "run":
            probe_parser.add_argument("--profile", default=None, help="AWS profile, Bedrock only")
            probe_parser.add_argument("--cap-usd", type=float, default=DEVELOPMENT_CAP_USD)
            probe_parser.add_argument("--allow-over-cap", action="store_true")
            probe_parser.add_argument("--max-minutes", type=float, default=30.0)
            probe_parser.add_argument("--store", choices=("local", "s3"), default="local")
            probe_parser.add_argument("--bucket", default=None)

    scenarios = groups.add_parser(
        "scenarios", help="Phase 2.5 scenarios and wordings. Offline; calls no model."
    )
    scenarios.add_argument("--root", type=Path, default=None, help=argparse.SUPPRESS)
    scenario_actions = scenarios.add_subparsers(dest="action", required=True)
    scenario_actions.add_parser(
        "render",
        help="Write each scenario and the cited public version from the sources and figures",
    )
    scenario_actions.add_parser(
        "check",
        help="Check the sources, that every rendered file is fresh, the templates and the log",
    )

    protocol = groups.add_parser(
        "protocol", help="Phase 3.5 pre-registration lock. Offline; calls no model and no AWS."
    )
    protocol.add_argument("--root", type=Path, default=None, help=argparse.SUPPRESS)
    protocol_actions = protocol.add_subparsers(dest="action", required=True)
    protocol_actions.add_parser(
        "check", help="Check the tree against the lock; passes when there is no lock yet"
    )
    lock_parser = protocol_actions.add_parser(
        "lock", help="Build the lock; with --write, create it (never over an existing one)"
    )
    lock_parser.add_argument("--write", action="store_true", help="write the file; else print it")
    lock_parser.add_argument(
        "--model",
        dest="models",
        action="append",
        default=[],
        metavar="KEY",
        help="an official model's key in models.toml; repeat for each, never inferred",
    )
    lock_parser.add_argument("--experiment", default=LOCK_EXPERIMENT, help=argparse.SUPPRESS)

    simulate = groups.add_parser(
        "simulate", help="Phase 3 simulations. Offline; calls no model and no AWS."
    )
    simulate.add_argument("--root", type=Path, default=None, help=argparse.SUPPRESS)
    simulate_actions = simulate.add_subparsers(dest="action", required=True)
    simulate_run = simulate_actions.add_parser(
        "run",
        help="Run every simulation into simulation-results.json (about an hour; --quick: seconds)",
    )
    simulate_run.add_argument(
        "--quick", action="store_true", help="a small slice of each family, written under scratch/"
    )
    simulate_run.add_argument("--workers", type=int, default=None, help="default: up to 12")
    simulate_report = simulate_actions.add_parser(
        "report",
        help="Write simulation-summary.md and matcher-calibration.md from the results file",
    )
    simulate_report.add_argument("--quick", action="store_true", help="report the quick run's file")
    return parser


SWEEP_COMMANDS = {
    "plan": cmd_sweep_plan,
    "run": cmd_sweep_run,
    "launch": cmd_sweep_launch,
    "status": cmd_sweep_status,
    "report": cmd_sweep_report,
    "stop": cmd_sweep_stop,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.group == "dossier":
        return cmd_dossier(args)
    if args.group == "scenarios":
        return cmd_scenarios(args)
    if args.group == "protocol":
        return cmd_protocol(args)
    if args.group == "simulate":
        if args.action == "run" and args.workers is None:
            args.workers = max(1, min(12, (os.cpu_count() or 2) - 2))
        return cmd_simulate(args)
    if args.group == "probes":
        try:
            return PROBE_COMMANDS[args.action](args)
        except (SweepRefusal, ExperimentError, ProbeError, FigureError, ScenarioSourceError) as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return REFUSED_EXIT
        except IdentityError as exc:
            print(f"cannot tell where this is running: {exc}", file=sys.stderr)
            return REFUSED_EXIT
        except (BotoCoreError, ClientError) as exc:
            print(f"AWS error: {exc}", file=sys.stderr)
            return REFUSED_EXIT
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
