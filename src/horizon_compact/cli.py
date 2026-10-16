"""``hc``: the harness command line. ``smoke`` (Phase 0.5) makes single recorded calls; ``sweep`` (Phase 1)
plans, runs, launches, inspects and stops a sweep; ``dossier`` (Phase 2) renders and checks the fictional
company's dossier and calls nothing; ``scenarios`` (Phase 2.5) renders and checks the four scenarios and
calls nothing. Every command that calls a model or authenticates to AWS is typed by him."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import signal
import subprocess
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import FrameType
from typing import Any

import boto3
import botocore
from botocore.exceptions import BotoCoreError, ClientError

import horizon_compact
from horizon_compact.casebuild.appendix import AppendixError, CaseAppendix, open_case
from horizon_compact.casebuild.assemble import BuildError, assemble_case, prepare_case
from horizon_compact.casebuild.cutoff import CutoffError
from horizon_compact.casebuild.documents import DocumentsError, build_document_set, write_sources
from horizon_compact.casebuild.edgar import EdgarClient, EdgarError, UrllibTransport
from horizon_compact.casebuild.edgar import user_agent as sec_user_agent
from horizon_compact.casebuild.extract import ExtractionError, build_requests
from horizon_compact.casebuild.extraction_model import (
    ExtractionModelError,
    entry_sha256,
    extraction_route,
    load_extraction_model,
)
from horizon_compact.casebuild.foreshadow import (
    ForeshadowError,
    find_hits,
    format_hits,
    parse_terms,
    write_hits,
)
from horizon_compact.casebuild.frozen import FrozenInputsError, frozen_inputs, git_in
from horizon_compact.casebuild.handfile import HandFileError, load_hand_boundaries
from horizon_compact.casebuild.options import OptionsError
from horizon_compact.casebuild.search import (
    CRITERIA,
    ISO_DATE,
    READ_REQUIRED,
    RULE_DATE,
    TYPES,
    K,
    LogError,
    Row,
    SearchError,
    SelectionLog,
    candidate_terms,
    load_newest_log,
    run_search,
    write_candidates,
    write_log_version,
)
from horizon_compact.casebuild.sections import build_section_inputs
from horizon_compact.casebuild.splitter import SplitRefused
from horizon_compact.casebuild.terms import CaseTerm, CaseTermsError, parse_case_terms
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
from horizon_compact.model_config import ModelConfig
from horizon_compact.privacy.guard import GuardError, load_configured_term_file
from horizon_compact.privacy.names import find_terms
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
from horizon_compact.protocol.cases import CaseContent, CaseError, case_lock_text, content_hashes
from horizon_compact.protocol.gate import (
    PilotRefusal,
    check_official,
    check_one_sweep_per_study,
    check_repeats,
    describe_decision,
    refusal_message,
    required_repeats,
    run_analysis_gate,
    run_gate,
    write_repeats,
)
from horizon_compact.protocol.lock import (
    EXPERIMENT as LOCK_EXPERIMENT,
)
from horizon_compact.protocol.lock import (
    EXPERIMENT_DIR,
    LOCK_RELATIVE,
    LockError,
    check_lock,
    lock_path,
    read_lock,
    render_lock,
    write_lock,
)
from horizon_compact.protocol.recordcheck import format_report as format_record_report
from horizon_compact.protocol.recordcheck import run_checks as run_record_checks
from horizon_compact.providers.anthropic import (
    AnthropicKeyError,
    AnthropicProvider,
)
from horizon_compact.providers.anthropic import read_key as read_anthropic_key
from horizon_compact.providers.anthropic import ssm_key_fetcher as anthropic_ssm_key_fetcher
from horizon_compact.providers.base import ModelRoute, Provider, TextProvider
from horizon_compact.providers.bedrock import REGION, BedrockConverseProvider, make_runtime_client
from horizon_compact.providers.ollama import DEFAULT_URL, OllamaProvider
from horizon_compact.providers.openrouter import (
    OpenRouterKeyError,
    OpenRouterProvider,
    read_key,
    ssm_key_fetcher,
)
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
from horizon_compact.sweep.awareness import (
    awareness_estimate,
    awareness_report,
    build_awareness_plan,
    check_awareness_cap,
    run_awareness,
)
from horizon_compact.sweep.blind import failures_view, format_report
from horizon_compact.sweep.identity import IdentityError, RunnerIdentity, identify
from horizon_compact.sweep.plan import (
    SweepPlan,
    SweepRefusal,
    build_plan,
    check_preflight,
    preflight_bound_usd,
    repeats_from_json,
    worst_case_per_attempt_usd,
)
from horizon_compact.sweep.prompt import render_prompt
from horizon_compact.sweep.refusals import make_calls, require_calls_before_analysis
from horizon_compact.sweep.runner import ROLES, Role, check_route, run_session, sweep_prefix
from horizon_compact.sweep.spend import DEVELOPMENT_CAP_USD
from horizon_compact.sweep.store import LocalStore, S3Store, Store
from horizon_compact.sweep.tokens import tokens_report
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


def _repeats_from_args(args: argparse.Namespace) -> int | dict[str, int]:
    """``--repeats N`` (the same count everywhere), ``--repeats-file`` (a repeats.json, read here) or
    ``--repeats-json`` (the same mapping as text, which is how a launch hands it to the task, since the task
    has no copy of the laptop's file). The parser allows exactly one."""
    if args.repeats is not None:
        return int(args.repeats)
    if args.repeats_file is not None:
        try:
            data = json.loads(Path(args.repeats_file).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SweepRefusal(f"cannot read the repeats file {args.repeats_file}: {exc}") from exc
        return repeats_from_json(data)
    try:
        return repeats_from_json(json.loads(args.repeats_json))
    except ValueError as exc:
        raise SweepRefusal(f"--repeats-json is not JSON: {exc}") from exc


def _role(args: argparse.Namespace) -> Role:
    """Where a session writes and what it labels its records: official, pilot or development. The parser
    allows at most one of ``--official`` and ``--pilot``."""
    if args.official:
        return "official"
    return "pilot" if args.pilot else "development"


def _check_pilot_sweep(args: argparse.Namespace, *, needed: bool) -> None:
    """``--pilot-sweep`` names the pilot whose ``repeats.json`` an official sweep must match: required with
    ``--official`` where the sweep is launched or run, and meaningless anywhere else."""
    if args.pilot_sweep and not args.official:
        raise SweepRefusal(
            "--pilot-sweep goes with --official: it names the pilot that set the repeats"
        )
    if needed and args.official and not args.pilot_sweep:
        raise SweepRefusal(
            "an official sweep needs --pilot-sweep <id>: the pilot whose repeats.json it must match "
            "(protocol 8.3)"
        )


def _load(args: argparse.Namespace) -> tuple[Experiment, SweepPlan]:
    root = Path(args.experiment_dir) if args.experiment_dir else None
    experiment = load_experiment(args.experiment, root)
    plan_ = build_plan(
        experiment,
        model_key=args.model,
        label=args.label,
        repeats=_repeats_from_args(args),
        seed=args.seed,
        scenarios=args.scenario or None,
        templates=args.template or None,
        # A pilot runs the tagged content on an official model, like the grid: the development-only refusals
        # in build_plan are for plans that are neither (the gate then checks the pilot's own rules).
        official=getattr(args, "official", False) or getattr(args, "pilot", False),
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


def _check_openrouter(
    args: argparse.Namespace, identity: RunnerIdentity, config: ModelConfig
) -> None:
    """An OpenRouter model runs in one of two places. On the laptop, with a key typed here, keeping its
    records here. In the container, only if its config names a pinned provider (so a call can never be served
    by another backend), with the key read from SSM and its records in the results bucket."""
    if identity.runner == "fargate":
        if not config.openrouter_provider:
            raise SweepRefusal(
                f"{args.model} is an OpenRouter model with no pinned provider: set openrouter_provider in "
                "models.toml before it runs in the container, so OpenRouter cannot serve it from another "
                "backend"
            )
        if args.store != "s3":
            raise SweepRefusal(
                "an OpenRouter model's runs in the container go to the results bucket"
            )
        return
    if args.store != "local":
        raise SweepRefusal("an OpenRouter model's runs stay on this laptop: use --store local")


def _check_anthropic(args: argparse.Namespace, identity: RunnerIdentity) -> None:
    """An Anthropic model runs in one of two places, like an OpenRouter one: on the laptop, with a key
    typed here, keeping its records here; in the container, with the key read from SSM and its records in the
    results bucket (Phase 4 code half section 4.9)."""
    if identity.runner == "fargate":
        if args.store != "s3":
            raise SweepRefusal(
                "an Anthropic model's runs in the container go to the results bucket"
            )
        return
    if args.store != "local":
        raise SweepRefusal("an Anthropic model's runs stay on this laptop: use --store local")


def _confirm_spend(
    estimate: Callable[[Store], SpendEstimate],
    model_key: str,
    cap_usd: float,
    store: Store,
    spender: str = "your own OpenRouter credit",
) -> None:
    """Print what the run is expected to cost and ask. Anything but ``y`` (or no answer at all) is a refusal,
    so nothing is sent and no key is asked for."""
    print(format_warning(model_key, estimate(store), cap_usd, spender))
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
    """The provider, route, store and account id for a run on this machine: a sweep or a probe run. A local
    model touches no AWS, and an OpenRouter model touches none on the laptop (in the container it reads its
    key from SSM); a Bedrock model needs a session."""
    config = experiment.model(model_key)
    provider: Provider
    if config.route == "openrouter":
        _check_openrouter(args, identity, config)
        route = ModelRoute(
            model_key,
            config.model_id,
            "openrouter",
            invoke_id=config.model_id,
            pinned_provider=config.openrouter_provider,
            reasoning_effort=config.reasoning_effort,
        )
        if identity.runner == "fargate":
            # The container: the task role reads the key from SSM, never a file, a command line or a prompt.
            session = _session(args, identity)
            account_id = session.client("sts").get_caller_identity()["Account"]
            try:
                key = read_key(
                    {},
                    ask=lambda: "",
                    ssm_fetch=ssm_key_fetcher(session.client("ssm")),
                )
            except OpenRouterKeyError as exc:
                raise SweepRefusal(str(exc)) from exc
            return OpenRouterProvider(key), route, _store(args, session), account_id
        # The laptop. No AWS session. The spend warning comes after every refusal and before the key, and the
        # key is asked for last, so a refused run never prompts; it lives in the provider and nowhere else.
        store = _store(args, None)
        _confirm_spend(estimate, model_key, cap_usd, store)
        try:
            provider = OpenRouterProvider(read_key(os.environ))
        except OpenRouterKeyError as exc:
            raise SweepRefusal(str(exc)) from exc
        return provider, route, store, LOCAL_ACCOUNT_ID
    if config.route == "anthropic":
        _check_anthropic(args, identity)
        route = ModelRoute(
            model_key,
            config.model_id,
            "anthropic",
            invoke_id=config.model_id,
            thinking_off=config.thinking == "off",
        )
        if identity.runner == "fargate":
            # The container: the task role reads the key from SSM, never a file, a command line or a prompt.
            session = _session(args, identity)
            account_id = session.client("sts").get_caller_identity()["Account"]
            try:
                key = read_anthropic_key(
                    {},
                    ask=lambda: "",
                    ssm_fetch=anthropic_ssm_key_fetcher(session.client("ssm")),
                )
            except AnthropicKeyError as exc:
                raise SweepRefusal(str(exc)) from exc
            return AnthropicProvider(key), route, _store(args, session), account_id
        # The laptop: no AWS session; the spend warning, then the key, as for OpenRouter.
        store = _store(args, None)
        _confirm_spend(
            estimate,
            model_key,
            cap_usd,
            store,
            "your prepaid Anthropic credit (workspace horizon-compact)",
        )
        try:
            provider = AnthropicProvider(read_anthropic_key(os.environ))
        except AnthropicKeyError as exc:
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
        f"{plan_.repeats_text()} repeats)"
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
    if not (args.official or args.pilot):
        raise SweepRefusal(
            "--dry-run checks an official sweep against the lock: add --official (or --pilot)"
        )
    _check_pilot_sweep(args, needed=False)
    experiment, plan_ = _load(args)
    result = run_gate(
        experiment,
        plan_,
        identify(os.environ, _laptop_git),
        require_container=False,
        pilot=args.pilot,
    )
    print(f"sweep:   {plan_.sweep_id} ({len(plan_.runs)} runs, model {plan_.model_key})")
    for note in result.notes:
        print(f"note: {note}")
    if not result.ok:
        print(refusal_message(result), file=sys.stderr)
        return REFUSED_EXIT
    print(
        f"{'pilot' if args.pilot else 'official sweep'}: every check passes "
        "(dry run; nothing written, nothing called)"
    )
    return CLEAN_EXIT


def cmd_sweep_run(args: argparse.Namespace) -> int:
    if args.dry_run:
        return cmd_sweep_dry_run(args)
    experiment, plan_ = _load(args)
    cap = _check_cap(args)
    _check_pilot_sweep(args, needed=False)
    identity = identify(os.environ, _laptop_git)
    if args.official or args.pilot:
        check_official(experiment, plan_, identity, pilot=args.pilot)
    _check_pilot_sweep(args, needed=True)  # after the gate, which names everything wrong at once
    # A session writes under its role's prefix and labels its records with it; nothing else does.
    role = _role(args)
    check_route(experiment, plan_.model_key, os.environ)
    check_preflight(experiment, plan_, cap)
    provider, route, store, account_id = _connect(
        args,
        experiment,
        plan_.model_key,
        identity,
        lambda store: sweep_estimate(experiment, plan_, store, role),
        cap,
    )
    if args.official:
        # The repeats the pilot set, read from the store the session writes to: a hand-typed command in the
        # container cannot skip them (protocol 8.3).
        check_repeats(store, plan_, args.pilot_sweep)
        check_one_sweep_per_study(store, plan_)

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
        role=role,
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
    if launch_route == "openrouter" and not experiment.model(plan_.model_key).openrouter_provider:
        raise SweepRefusal(
            f"{plan_.model_key} is an OpenRouter model with no pinned provider: it runs on this laptop with "
            "a key typed here (`hc sweep run`), or set openrouter_provider in models.toml to launch it"
        )
    cap = _check_cap(args)
    _check_pilot_sweep(args, needed=False)
    session = None
    if args.official or args.pilot:
        # The laptop checks 1-7 before anything starts; the task checks all eight again in the container.
        preflight = run_gate(
            experiment,
            plan_,
            identify({}, _laptop_git),
            require_container=False,
            why="launch",
            pilot=args.pilot,
        )
        if not preflight.ok:
            raise SweepRefusal(refusal_message(preflight))
    _check_pilot_sweep(args, needed=True)
    if args.official:
        # The pilot's repeats.json is read here, from the bucket, so a launch that would be refused in the
        # container is refused before it starts.
        session = _session(args, identify({}, _laptop_git))
        official_store = _store(args, session)
        check_repeats(official_store, plan_, args.pilot_sweep)
        check_one_sweep_per_study(official_store, plan_)
    check_preflight(experiment, plan_, cap)
    session = session or _session(args, identify({}, _laptop_git))
    command = [
        "sweep", "run",
        "--experiment", args.experiment,
        "--model", args.model,
        "--seed", str(args.seed),
        "--label", args.label,
        "--store", "s3",
        "--cap-usd", str(cap),
        "--max-minutes", str(args.max_minutes),
    ]  # fmt: skip
    if args.repeats is not None:
        command += ["--repeats", str(args.repeats)]
    else:  # the task has no copy of a laptop file, so the mapping travels in the command
        command += ["--repeats-json", json.dumps(dict(plan_.repeats))]
    for scenario_id in args.scenario or []:
        command += ["--scenario", scenario_id]
    for template_id in args.template or []:
        command += ["--template", template_id]
    if args.allow_over_cap:
        command.append("--allow-over-cap")
    if args.official:
        command += ["--official", "--pilot-sweep", args.pilot_sweep]
    elif args.pilot:
        command.append("--pilot")
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
    summary = sweep_status.summarize(_store(args, session), args.experiment, sweep_id, args.role)
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


def cmd_sweep_awareness(args: argparse.Namespace) -> int:
    """The awareness probe (protocol 9.6): S1, every objective under every template, one call each, no tool.
    Official only, so the gate applies as for the grid: ``--dry-run`` checks it, ``--launch`` starts the
    container task, and a plain run is what the task executes. ``--report`` quotes every stored reply."""
    root = Path(args.experiment_dir) if args.experiment_dir else None
    experiment = load_experiment(args.experiment, root)
    plan_ = build_awareness_plan(experiment, args.model, args.seed)
    if args.report:
        session = None if args.store == "local" else _session(args, identify({}, _laptop_git))
        print(awareness_report(_store(args, session), experiment, plan_))
        return CLEAN_EXIT
    cap = _check_cap(args)
    route_kind = experiment.model(plan_.model_key).route
    if route_kind == "local":
        raise SweepRefusal(
            f"{plan_.model_key} is a local model: the awareness probe is official only"
        )
    if args.dry_run or args.launch:
        # The laptop checks 1-7 before anything starts; the task checks all eight again in the container.
        preflight = run_gate(
            experiment,
            plan_,
            identify({} if args.launch else os.environ, _laptop_git),
            require_container=False,
            why="launch" if args.launch else "dry run",
        )
        for note in preflight.notes:
            print(f"note: {note}")
        if not preflight.ok:
            if args.launch:
                raise SweepRefusal(refusal_message(preflight))
            print(refusal_message(preflight), file=sys.stderr)
            return REFUSED_EXIT
        check_awareness_cap(experiment, plan_, cap)
        if args.dry_run:
            print(f"awareness: {plan_.sweep_id} ({len(plan_.runs)} calls, model {plan_.model_key})")
            print("every check passes (dry run; nothing written, nothing called)")
            return CLEAN_EXIT
        if route_kind == "openrouter" and not experiment.model(plan_.model_key).openrouter_provider:
            raise SweepRefusal(
                f"{plan_.model_key} is an OpenRouter model with no pinned provider: set "
                "openrouter_provider in models.toml before it runs in the container"
            )
        session = _session(args, identify({}, _laptop_git))
        command = [
            "sweep", "awareness",
            "--experiment", args.experiment,
            "--model", args.model,
            "--seed", str(args.seed),
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
        print("read it back:    hc sweep awareness --report (same arguments, --store s3)")
        return CLEAN_EXIT
    identity = identify(os.environ, _laptop_git)
    check_official(experiment, plan_, identity)
    check_route(experiment, plan_.model_key, os.environ)
    check_awareness_cap(experiment, plan_, cap)
    provider, route, store, account_id = _connect(
        args,
        experiment,
        plan_.model_key,
        identity,
        lambda store: awareness_estimate(experiment, plan_, store),
        cap,
    )
    if not isinstance(provider, BedrockConverseProvider | OpenRouterProvider | AnthropicProvider):
        raise SweepRefusal(f"{plan_.model_key}'s provider cannot make a call with no tool")

    stop_requested = {"flag": False}

    def request_stop(signum: int, frame: FrameType | None) -> None:
        stop_requested["flag"] = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    result = run_awareness(
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
        f"calls recorded:  {result.calls_done_before + result.calls_done_now} of {result.calls_total}"
    )
    print(f"this session:    {result.api_calls_now} calls, ${result.cost_usd_now:.4f}")
    print(f"sweep total:     ${result.cost_usd_total:.4f} (cap ${cap:.2f})")
    return CLEAN_EXIT if result.clean else NOT_CLEAN_EXIT


def cmd_sweep_refusals(args: argparse.Namespace) -> int:
    """The blind refusal calls (protocol 4.7): every ``no_tool_call`` run of a finished sweep, as a masked,
    shuffled case with only the reply's text, asked once, written once, before any official analysis."""
    session = None if args.store == "local" else _session(args, identify({}, _laptop_git))
    store = _store(args, session)
    prefix = sweep_prefix(args.experiment, args.sweep, args.role)

    def ask(prompt: str) -> str:
        return input(prompt)

    result = make_calls(
        store,
        prefix,
        args.sweep,
        made_by=args.made_by,
        ask=ask,
        show=print,
    )
    if result.calls_key is not None:
        print(f"wrote {result.calls_key} ({result.refusals} of {result.cases} called refusals)")
        print(f"wrote {result.meta_key}")
    return CLEAN_EXIT


def cmd_analyze(args: argparse.Namespace) -> int:
    """One finished sweep to one results file (Phase 4 code half section 4.7). The analysis needs scipy, which
    the container image leaves out, so it is imported here and never at module level."""
    from horizon_compact.analysis.failures import RefusalCallError, read_refusal_calls
    from horizon_compact.analysis.records import RecordRefusal, read_runs
    from horizon_compact.analysis.results import build_results, write_results

    top = Path(args.root) if args.root else Path(_git("rev-parse", "--show-toplevel"))
    protocol = args.protocol
    if protocol is None:
        try:
            protocol = read_lock(lock_path(top)).protocol
        except LockError as exc:
            raise SweepRefusal(
                "no --protocol given and no readable lock to take it from: "
                + "; ".join(exc.reasons)
            ) from exc
    experiment = load_experiment(
        args.experiment, Path(args.experiment_dir) if args.experiment_dir else None
    )
    if args.role == "official":
        frozen = run_analysis_gate(experiment)
        if not frozen.ok:
            raise SweepRefusal(
                "\n".join(
                    ["official analysis refused: the analysis must be the locked one"]
                    + [f"  {line}" for line in [*frozen.failures, *frozen.notes]]
                )
            )
    session = None if args.store == "local" else _session(args, identify({}, _laptop_git))
    store = _store(args, session)
    prefix = sweep_prefix(experiment.name, args.sweep, args.role)
    try:
        runset = read_runs(store, prefix)
    except RecordRefusal as exc:
        raise SweepRefusal(str(exc)) from exc
    # The calls come first: a sweep with a no_tool_call run and no calls file is refused here.
    require_calls_before_analysis(store, prefix, runset.rows)
    try:
        calls = read_refusal_calls(store, prefix)
    except RefusalCallError as exc:
        raise SweepRefusal(str(exc)) from exc
    try:
        # The RunSet itself goes in, so its refusal of unfinished runs cannot be skipped. The analysis
        # refuses data it cannot assess (unfinished runs, a cell too small for a variance) with ValueError.
        results = build_results(experiment, runset, calls=calls)
    except ValueError as exc:
        raise SweepRefusal(f"the analysis refused this sweep: {exc}") from exc
    try:
        path = write_results(results, top, protocol)
    except (FileExistsError, ValueError) as exc:
        raise SweepRefusal(str(exc)) from exc
    print(f"wrote {path.relative_to(top)}")
    print(
        f"sweep:           {results.sweep_id} ({results.model_key}, {len(runset.rows)} runs, "
        f"{len(results.refusal_calls)} refusal calls)"
    )
    print(
        "commit it yourself; it is never overwritten, and a different analysis is a new protocol version"
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
        (f"{plan_.sweep_id}.md", format_report(store, experiment, plan_, args.role)),
        (f"{plan_.sweep_id}-failures.md", failures_view(store, experiment, plan_, args.role)),
    ):
        path = folder / name
        path.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(top)}")
    return CLEAN_EXIT


def cmd_sweep_tokens(args: argparse.Namespace) -> int:
    """What thinking cost, in tokens, per S1 cell (Phase 4 runs half section 5.2). Reads token counts and
    block counts only; run at the reveal."""
    session = None if args.store == "local" else _session(args, identify({}, _laptop_git))
    print(tokens_report(_store(args, session), args.experiment, args.sweep, args.vs))
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


# --- case (Phase 5 step 6) --------------------------------------------------------------------------------


def _case_text(path: Path, what: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AppendixError(f"cannot read {what}: {exc.strerror or type(exc).__name__}") from exc


def cmd_case_foreshadow(args: argparse.Namespace) -> int:
    case = open_case(args.label)
    texts = {
        "dossier": _case_text(case.dossier_path, "the case's dossier.toml"),
        "scenario": _case_text(case.scenario_path, "the case's scenario.toml"),
    }
    terms_text = _case_text(args.terms, "the term file")
    hits = find_hits(texts, parse_terms(terms_text))
    name = write_hits(case, hits, terms_text=terms_text, texts=texts)
    if hits:
        print(format_hits(hits), file=sys.stderr)
        print(f"{len(hits)} hit(s), written to {name}: justify each in writing or remove it.")
        return CHECK_FAILED_EXIT
    print(f"foreshadow check: no hits ({name})")
    return CLEAN_EXIT


def cmd_case_hashes(args: argparse.Namespace) -> int:
    case = open_case(args.label)
    try:
        content = CaseContent(
            dossier=case.dossier_path.read_bytes(),
            scenario=case.scenario_path.read_bytes(),
            rubric=args.rubric.read_bytes(),
        )
    except OSError as exc:
        raise AppendixError(
            f"cannot read a case file: {exc.strerror or type(exc).__name__}"
        ) from exc
    print(case_lock_text(args.label, args.probe_set, content_hashes(content)), end="")
    return CLEAN_EXIT


def _today() -> date:
    """The local date; a function so the tests can set it."""
    return date.today()


def cmd_case_search(args: argparse.Namespace) -> int:
    """The search of protocol §12.3, once (search-half IMPLEMENTATION doc §4.4). Prints counts only."""
    today = _today()
    if args.date != today:
        raise SearchError(f"--date {args.date.isoformat()} is not today ({today.isoformat()})")
    if today < RULE_DATE:
        raise SearchError(
            f"the search runs on {RULE_DATE.isoformat()} by rule (protocol §12.2), not before"
        )
    deviation = (args.deviation or "").strip()
    if today != RULE_DATE and not deviation:
        raise SearchError(
            f"the rule date was {RULE_DATE.isoformat()}: a later search is a deviation, so give "
            '--deviation "<the reason>"'
        )
    case = open_case("search")
    if (case.directory / "candidates.json").exists():
        raise SearchError("the search has already run: candidates.json exists, and it runs once")
    client = EdgarClient(appendix=case, transport=UrllibTransport(), user_agent=sec_user_agent())
    result = run_search(client, RULE_DATE)
    record = {**result.record, "run_on": today.isoformat(), "deviation": deviation or None}
    result = dataclasses.replace(result, record=record)
    write_candidates(case, result)
    log_name = write_log_version(case, SelectionLog.start(result.candidates))
    print(f"search: window to {result.end.isoformat()}, run on {today.isoformat()}")
    for query in record["queries"]:
        dropped = ", ".join(f"{n} {why}" for why, n in sorted(query["dropped"].items())) or "none"
        print(
            f"  channel {query['channel']} {query['query']}: {query['total']} documents, "
            f"{query['pages']} pages, {query['filings_kept']} filings kept; dropped: {dropped}"
        )
    for key, count in record["candidates"].items():
        print(f"  {key}: {count} candidates")
    print(f"written: candidates.json and {log_name} in the appendix's search folder")
    return CLEAN_EXIT


def _log_candidates(case: CaseAppendix) -> dict[str, dict[str, Any]]:
    """The private candidate list by id, for ``show``; empty if the search folder has none."""
    path = case.directory / "candidates.json"
    if not path.exists():
        return {}
    try:
        return {c["id"]: c for c in json.loads(path.read_text(encoding="utf-8"))["list"]}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise LogError(f"candidates.json cannot be read: {type(exc).__name__}") from exc


def _log_status(row: Row) -> str:
    parts = []
    for criterion in CRITERIA:
        if criterion not in row.results:
            continue
        result = row.results[criterion]
        word = (
            "pass"
            if result.result == "pass"
            else "FAIL (disputed, does not stand)"
            if row.disputed(criterion)
            else "FAIL"
        )
        parts.append(f"{criterion} {word}" + (f" {result.disclosed}" if result.disclosed else ""))
    # a rejection on 3, 4 or 5, whether it stands or the reader disputed it
    for criterion in READ_REQUIRED:
        if criterion in row.results and row.results[criterion].result == "fail":
            read = row.reads.get(criterion)
            parts.append(
                "read: " + ("NOT YET" if read is None else "agrees" if read.agrees else "DISAGREES")
            )
    next_criterion = next((c for c in CRITERIA if c not in row.results), None)
    if row.failed:
        parts.append("finished: rejected")
    elif next_criterion is None:
        parts.append("finished: passed all")
    else:
        parts.append(f"next: {next_criterion}")
    return " | ".join(parts)


def _log_show(case: CaseAppendix, log: SelectionLog, case_type: str) -> None:
    """For his terminal only: the private candidate details beside the log's state. Names appear here."""
    details = _log_candidates(case)
    chosen = log.selection(case_type)
    print(f"{case_type} (k={K[case_type]}): cases {', '.join(chosen.cases) or 'none yet'}")
    for row in log.rows.values():
        if row.type != case_type:
            continue
        found = details.get(row.id, {})
        names = "; ".join(found.get("names", [])) or "(no name on file)"
        print(f"  {row.id} {row.pool} filed {found.get('file_date', '?')} {row.accession} {names}")
        print(f"      {_log_status(row)}")
    for line in chosen.waiting:
        print(f"  waiting: {line}")
    if chosen.complete:
        print(f"  selection complete; shortfall {chosen.shortfall}")
    for line in log.problems():
        print(f"  open: {line}")


def _check_public_reason(text: str, details: dict[str, dict[str, Any]]) -> None:
    """A public reason goes into the public view, so it is refused, before anything is written, if it holds a
    name-guard term, any candidate's name, ticker, CIK or accession number, or a date. Fails closed: with no
    term file or no candidate list it cannot be checked, so it is refused. Says which, never the match."""
    if not text.strip():
        raise LogError("a public reason, when given, is not blank")
    if not details:
        raise LogError("candidates.json is missing, so a public reason cannot be checked")
    try:
        term_file = load_configured_term_file()
    except GuardError as exc:
        raise LogError(f"a public reason cannot be checked without the name guard: {exc}") from exc
    if find_terms(text, term_file):
        raise LogError("the public reason holds a term from the name guard's list")
    for candidate_id, record in details.items():
        if any(term.pattern.search(text) for term in candidate_terms(record)):
            raise LogError(f"the public reason holds {candidate_id}'s name or number")
    if ISO_DATE.search(text):
        raise LogError("the public reason holds a date; the public view carries none")


def cmd_case_log(args: argparse.Namespace) -> int:
    """The selection log from the terminal (search-half IMPLEMENTATION doc §4.3): `show` and `public` read the
    newest version; `record` and `read` apply exactly one change and write the next, never an earlier one."""
    case = open_case("search")
    log = load_newest_log(case)
    if args.log_action == "show":
        _log_show(case, log, args.type)
        return CLEAN_EXIT
    if args.log_action == "public":
        view = {args.type: log.public_view()[args.type]}
        print(json.dumps(view, indent=2, ensure_ascii=False))
        return CLEAN_EXIT
    row = log.rows.get(args.id)
    if row is None:
        raise LogError(f"no candidate {args.id!r} in the log")
    if row.type != args.type:
        raise LogError(f"{args.id} is a {row.type} candidate, not {args.type}")
    if args.log_action == "record":
        if args.public_reason is not None:
            _check_public_reason(args.public_reason, _log_candidates(case))
        log.record(
            args.id,
            args.criterion,
            args.result,
            args.reason,
            public_reason=args.public_reason,
            disclosed=args.disclosed,
        )
        what = f"{args.criterion} {args.result}"
    else:
        log.record_read(
            args.id, args.criterion, agrees=args.verdict == "agree", resolution=args.resolution
        )
        what = f"read of {args.criterion}: {args.verdict}"
    name = write_log_version(case, log)
    print(f"{args.id}: {what}; wrote {name}")
    print(f"  {_log_status(log.rows[args.id])}")
    return CLEAN_EXIT


def _extraction_provider() -> TextProvider:
    """Anthropic's API with the prepaid-credit key, from ``ANTHROPIC_API_KEY`` or a hidden prompt; a function
    so the tests can set it. Never reached before every refusal that needs no network or key."""
    return AnthropicProvider(read_anthropic_key(os.environ))


def _case_terms(case: CaseAppendix) -> tuple[CaseTerm, ...]:
    try:
        return parse_case_terms(case.terms_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CaseTermsError(
            f"the case's term list {case.terms_path.name} cannot be read ({type(exc).__name__}): "
            "write it in the case's folder before the build"
        ) from exc


def _build_candidate(search: CaseAppendix, label: str, cutoff: date) -> str:
    """The CIK of ``label``, from the search's candidate list and never the command line, after checking the
    selection log: criteria 1-4 passed (search-half doc §4.1 step 1), and the cut-off is the day before the
    first disclosure the log recorded (protocol §12.6)."""
    try:
        records = json.loads((search.directory / "candidates.json").read_text(encoding="utf-8"))[
            "list"
        ]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SearchError(
            f"candidates.json cannot be read ({type(exc).__name__}): has the search run?"
        ) from exc
    found = next((r for r in records if r.get("id") == label), None)
    if found is None:
        raise SearchError(f"{label} is not a candidate in the search's list")
    ciks = [str(c) for c in found.get("ciks", [])]
    if len(ciks) != 1:
        raise SearchError(f"{label} has {len(ciks)} CIKs in the list; a case needs exactly one")
    row = load_newest_log(search).rows.get(label)
    if row is None:
        raise LogError(f"{label} is not in the selection log")
    # Protocol §12.4's criteria 1-4 and the first-disclosure check before them: every criterion but the
    # probe (criterion 5, ``not_recognizable``), which needs the dossier this command builds.
    unpassed = [c for c in CRITERIA[:-1] if not row.met(c)]
    if unpassed:
        raise LogError(f"{label} has not passed {', '.join(unpassed)} in the selection log")
    assert row.disclosed is not None  # a passed first_disclosure always carries its date
    expected = row.disclosed - timedelta(days=1)
    if cutoff != expected:
        raise SearchError(
            f"the cut-off is the day before first disclosure (protocol §12.6): the log gives "
            f"{expected.isoformat()} for {label}, not {cutoff.isoformat()}"
        )
    return ciks[0]


def cmd_case_build(args: argparse.Namespace) -> int:
    """Build a case's sections once (search-half doc §4.5): every refusal that needs no network comes first,
    then the filings (cached), then the key, then the extraction, then the write. The seed is drawn by
    ``scale.new_seed`` inside ``prepare_case``; nothing here can supply one."""
    case = open_case(args.label)
    search = open_case("search")
    cik = _build_candidate(search, args.label, args.cutoff)
    terms = _case_terms(case)
    hand, hand_sha = load_hand_boundaries(case.hand_boundaries_path)
    model_key, model = load_extraction_model()
    assert model.max_tokens is not None  # an extraction entry always has one (ModelConfig checks)
    provenance = {
        **frozen_inputs(git_in(default_repo_root())),
        "extraction_model": model_key,
        "extraction_entry_sha256": entry_sha256(model_key, model),
        "hand_boundaries_sha256": hand_sha,
    }
    for path in (case.sections_path, case.flags_template_path, case.build_path):
        if path.exists():
            raise BuildError(
                f"{path.name} already exists: this case was prepared; clear its folder by hand to start over"
            )

    client = EdgarClient(appendix=case, transport=UrllibTransport(), user_agent=sec_user_agent())
    docset = build_document_set(client, cik, args.cutoff)
    try:
        inputs = build_section_inputs(
            docset, shape=args.shape, hand=hand
        )  # before any key or model call
    except SplitRefused as exc:
        print(
            f"needs hand boundaries: {exc}\n"
            f"Write {case.hand_boundaries_path.name} in the case's folder (accession number -> item key -> "
            "[start, end] offsets in the filing's extracted text), then run the same command again; the "
            "filings are cached.",
            file=sys.stderr,
        )
        return REFUSED_EXIT
    write_sources(case, docset)
    requests = build_requests(inputs)
    print(
        f"{args.label}: {args.shape}, cut-off {args.cutoff.isoformat()}, "
        f"{len(docset.source_records())} source documents, {len(requests)} extraction requests "
        f"to {model_key}"
    )
    provider = _extraction_provider()
    prepared = prepare_case(
        case,
        docset,
        shape=args.shape,
        terms=terms,
        provider=provider,
        route=extraction_route(model_key, model),
        hand=hand,
        max_tokens=model.max_tokens,
        provenance=provenance,
    )
    replies = prepared.record["extraction"]["replies"].values()
    tokens_in = sum(r["usage"]["input_tokens"] for r in replies)
    tokens_out = sum(r["usage"]["output_tokens"] for r in replies)
    cost = (tokens_in * model.prices.input + tokens_out * model.prices.output) / 1_000_000
    print(
        f"extraction: {tokens_in:,} input and {tokens_out:,} output tokens, about ${cost:.2f} of credit"
    )
    print(
        f"sections: {', '.join(str(n) for n in sorted(prepared.sections))}; flags to review: {len(prepared.flags)}"
    )
    print("seed, factor and every record are in build.json")
    print(
        f"next: fill in {case.flags_template_path.name}, save it as {case.reviewed_flags_path.name}, "
        f"then `hc case assemble {args.label}`"
    )
    return CLEAN_EXIT


def cmd_case_assemble(args: argparse.Namespace) -> int:
    """Write the dossier once every flag has a current decision (search-half doc §4.5)."""
    case = open_case(args.label)
    assembled = assemble_case(case, terms=_case_terms(case))
    print(
        f"{args.label}: dossier.toml and assembly.json written; "
        f"{len(assembled.record['decisions'])} decisions applied; "
        f"dossier sha256 {assembled.dossier_sha256[:16]}"
    )
    return CLEAN_EXIT


def cmd_case(args: argparse.Namespace) -> int:
    try:
        if args.action == "build":
            return cmd_case_build(args)
        if args.action == "assemble":
            return cmd_case_assemble(args)
        if args.action == "search":
            return cmd_case_search(args)
        if args.action == "log":
            return cmd_case_log(args)
        return cmd_case_foreshadow(args) if args.action == "foreshadow" else cmd_case_hashes(args)
    except (
        AppendixError,
        ForeshadowError,
        CaseError,
        SearchError,
        EdgarError,
        LogError,
        BuildError,
        DocumentsError,
        CutoffError,
        ExtractionError,
        ExtractionModelError,
        CaseTermsError,
        OptionsError,
        HandFileError,
        FrozenInputsError,
        AnthropicKeyError,
        SplitRefused,
    ) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return REFUSED_EXIT


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


def cmd_protocol_repeats(args: argparse.Namespace, root: Path) -> int:
    """Set the repeats from a finished pilot and write ``repeats.json`` beside its records, once (Phase 4 code
    half, section 4.3). Prints what the record holds and nothing that shows a direction."""
    try:
        lock = read_lock(lock_path(root))
    except LockError as exc:
        for reason in exc.reasons:
            print(f"refused: {reason}", file=sys.stderr)
        return REFUSED_EXIT
    experiment = load_experiment(lock.content.experiment, root / EXPERIMENT_DIR)
    session = None if args.store == "local" else _session(args, identify({}, _laptop_git))
    store = _store(args, session)
    prefix = sweep_prefix(experiment.name, args.pilot, "pilot")
    try:
        decision = required_repeats(store, prefix, experiment, lock)
        key = write_repeats(store, prefix, decision)
    except PilotRefusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return REFUSED_EXIT
    for line in describe_decision(decision):
        print(line)
    print(f"written: {key}")
    return CLEAN_EXIT


RECORD_CHECKS_FILE = "docs/phases/evidence/phase-4/record-checks.md"


def cmd_protocol_records(args: argparse.Namespace, root: Path) -> int:
    """The record checks (Phase 4 runs half section 5.3): read-only over every pilot and official sweep,
    writing one evidence file of counts, ids, hashes and dates. Never reads a decision, a choice, a memo or
    a reply."""
    try:
        lock = read_lock(lock_path(root))
    except LockError as exc:
        for reason in exc.reasons:
            print(f"refused: {reason}", file=sys.stderr)
        return REFUSED_EXIT
    session = None if args.store == "local" else _session(args, identify({}, _laptop_git))
    store = _store(args, session)
    report = run_record_checks(store, lock, list(check_lock(root).failures))
    sha, dirty = _laptop_git()
    text = format_record_report(
        report,
        protocol=lock.protocol,
        tree=f"{sha[:12]}{' plus uncommitted changes' if dirty else ''}",
        made_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    target = root / RECORD_CHECKS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    for check in report.checks:
        print(f"{'reported' if check.info else ('pass' if check.ok else 'FAIL'):<9}{check.name}")
    print(f"written: {RECORD_CHECKS_FILE}")
    return CLEAN_EXIT if report.ok else CHECK_FAILED_EXIT


def cmd_protocol(args: argparse.Namespace) -> int:
    root: Path = args.root or default_repo_root()
    if args.action == "check":
        return cmd_protocol_check(root)
    if args.action == "records":
        return cmd_protocol_records(args, root)
    if args.action == "repeats":
        return cmd_protocol_repeats(args, root)
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
    repeats = parser.add_mutually_exclusive_group(required=True)
    repeats.add_argument("--repeats", type=int, help="the same count for every scenario")
    repeats.add_argument(
        "--repeats-file", default=None, help="a repeats.json: a count for each scenario"
    )
    repeats.add_argument("--repeats-json", default=None, help=argparse.SUPPRESS)
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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--official", action="store_true", help="checked against experiment/protocol/prereg.lock"
    )
    mode.add_argument(
        "--pilot",
        action="store_true",
        help="the pilot (two development wordings, label pilot), checked against the lock; writes under pilot/",
    )
    parser.add_argument(
        "--pilot-sweep",
        default=None,
        metavar="ID",
        help="with --official: the pilot whose repeats.json the plan's repeats must equal",
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
    launch_parser.set_defaults(store="s3")
    launch_parser.add_argument(
        "--bucket", default=None, help="the results bucket (to read the pilot's repeats.json)"
    )
    status_parser = sweep_actions.add_parser("status", help="Summarize a sweep's stored objects")
    _add_plan_arguments(status_parser)
    status_parser.add_argument("--sweep-id", default=None, help="instead of the plan arguments")
    status_parser.add_argument("--store", choices=("local", "s3"), default="s3")
    status_parser.add_argument("--bucket", default=None)
    status_parser.add_argument("--profile", default=None)
    status_parser.add_argument("--role", choices=ROLES, default="development")
    report_parser = sweep_actions.add_parser(
        "report",
        help="Write the blind format report and the failures view. No amounts, choices or memos.",
    )
    _add_plan_arguments(report_parser)
    report_parser.add_argument("--store", choices=("local", "s3"), default="local")
    report_parser.add_argument("--bucket", default=None)
    report_parser.add_argument("--profile", default=None)
    report_parser.add_argument("--role", choices=ROLES, default="development")
    awareness_parser = sweep_actions.add_parser(
        "awareness",
        help="The awareness probe (protocol 9.6): S1, every objective and template, one call each, no tool",
    )
    awareness_parser.add_argument("--experiment", required=True)
    awareness_parser.add_argument("--model", required=True, help="a key in experiment/models.toml")
    awareness_parser.add_argument("--seed", type=int, required=True)
    awareness_parser.add_argument("--experiment-dir", default=None, help=argparse.SUPPRESS)
    awareness_parser.add_argument("--profile", default=None)
    awareness_parser.add_argument("--cap-usd", type=float, default=DEVELOPMENT_CAP_USD)
    awareness_parser.add_argument("--allow-over-cap", action="store_true")
    awareness_parser.add_argument("--max-minutes", type=float, default=30.0)
    awareness_parser.add_argument("--store", choices=("local", "s3"), default="s3")
    awareness_parser.add_argument("--bucket", default=None)
    awareness_mode = awareness_parser.add_mutually_exclusive_group()
    awareness_mode.add_argument(
        "--dry-run", action="store_true", help="every gate check; write nothing, call nothing"
    )
    awareness_mode.add_argument(
        "--launch", action="store_true", help="start the probe as a Fargate task"
    )
    awareness_mode.add_argument(
        "--report", action="store_true", help="print every stored reply in full"
    )
    refusals_parser = sweep_actions.add_parser(
        "refusals",
        help="Make the blind refusal calls for a finished sweep (once, before any analysis)",
    )
    refusals_parser.add_argument("--experiment", required=True)
    refusals_parser.add_argument("--sweep", required=True, help="the sweep id")
    refusals_parser.add_argument("--made-by", required=True, help="who is making the calls")
    refusals_parser.add_argument("--role", choices=("official", "development"), default="official")
    refusals_parser.add_argument("--store", choices=("local", "s3"), default="s3")
    refusals_parser.add_argument("--bucket", default=None)
    refusals_parser.add_argument("--profile", default=None)
    tokens_parser = sweep_actions.add_parser(
        "tokens",
        help="The thinking sub-study's token cost against the grid's matching cells. Counts only; run at the reveal.",
    )
    tokens_parser.add_argument("--experiment", required=True)
    tokens_parser.add_argument("--sweep", required=True, help="the grid's sweep id")
    tokens_parser.add_argument("--vs", required=True, help="the thinking sub-study's sweep id")
    tokens_parser.add_argument("--store", choices=("local", "s3"), default="s3")
    tokens_parser.add_argument("--bucket", default=None)
    tokens_parser.add_argument("--profile", default=None)
    stop_parser = sweep_actions.add_parser("stop", help="Stop a model's running sweep task")
    stop_parser.add_argument("--model", required=True)
    stop_parser.add_argument("--profile", default=None)

    analyze = groups.add_parser(
        "analyze",
        help="One finished sweep to one results file under experiment/results/. Needs the refusal calls first.",
    )
    analyze.add_argument("--experiment", required=True)
    analyze.add_argument("--sweep", required=True, help="the sweep id")
    analyze.add_argument("--role", choices=("official", "development"), default="official")
    analyze.add_argument("--store", choices=("local", "s3"), default="s3")
    analyze.add_argument("--bucket", default=None)
    analyze.add_argument("--profile", default=None)
    analyze.add_argument("--protocol", default=None, help="default: the lock's protocol name")
    analyze.add_argument("--root", default=None, help=argparse.SUPPRESS)
    analyze.add_argument("--experiment-dir", default=None, help=argparse.SUPPRESS)

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

    case = groups.add_parser(
        "case",
        help="Phase 5 case files in the private appendix. Offline; reads local files only.",
    )
    case_actions = case.add_subparsers(dest="action", required=True)
    foreshadow = case_actions.add_parser(
        "foreshadow",
        help="Search the case's dossier and scenario text for the rubric's key terms (one per line)",
    )
    foreshadow.add_argument("label", help="the case's neutral label, such as closure-1")
    foreshadow.add_argument(
        "--terms", type=Path, required=True, help="a file of terms, one per line"
    )
    hashes = case_actions.add_parser(
        "hashes", help="Print case.lock for the case's dossier, scenario text and a rubric file"
    )
    hashes.add_argument("label", help="the case's neutral label, such as closure-1")
    hashes.add_argument("--rubric", type=Path, required=True, help="the rubric file")
    hashes.add_argument("--probe-set", type=int, choices=(1, 2), default=1)
    search = case_actions.add_parser(
        "search",
        help="The real-case search of protocol §12.3, run once on the rule date. Reads the SEC; "
        "writes candidates into the appendix; prints counts only.",
    )
    search.add_argument(
        "--date", type=date.fromisoformat, required=True, help="today's date, YYYY-MM-DD"
    )
    search.add_argument("--deviation", help="the reason, if the search runs after the rule date")
    build = case_actions.add_parser(
        "build",
        help="Build a case's sections once from its candidate's pre-cut-off filings: fetches the SEC, calls "
        "the extraction model, writes the appendix. The CIK comes from the search's list; the seed is drawn.",
    )
    build.add_argument("label", help="the candidate's neutral id, such as closure-01")
    build.add_argument(
        "--cutoff",
        type=date.fromisoformat,
        required=True,
        help="YYYY-MM-DD: the day before first disclosure, as the selection log recorded it",
    )
    build.add_argument("--shape", choices=("S1", "S2", "S3", "S4"), required=True)
    assemble = case_actions.add_parser(
        "assemble",
        help="Write the case's dossier once every flag has a decision in reviewed-flags.json",
    )
    assemble.add_argument("label", help="the candidate's neutral id, such as closure-01")
    log = case_actions.add_parser(
        "log",
        help="The selection log (protocol §12.4) in the appendix: show, record a criterion, record the "
        "independent reader's read, or print the public view. Each change writes the next version.",
    )
    log.add_argument("type", choices=TYPES)
    log_actions = log.add_subparsers(dest="log_action", required=True)
    log_actions.add_parser(
        "show", help="Candidates and their state, with names: for the terminal only"
    )
    log_actions.add_parser("public", help="The public view, with no name; writes nothing")
    record = log_actions.add_parser(
        "record", help="The next criterion for a candidate, with its reason"
    )
    record.add_argument("id", help="the candidate's neutral id, such as closure-01")
    record.add_argument("criterion", choices=CRITERIA)
    record.add_argument("result", choices=("pass", "fail"))
    record.add_argument("--reason", required=True, help="private: it may name the company")
    record.add_argument(
        "--public-reason",
        help="optional, goes in the public view: no name, date, figure or place that identifies",
    )
    record.add_argument(
        "--disclosed",
        type=date.fromisoformat,
        help="YYYY-MM-DD; with a passed first_disclosure, and only then",
    )
    read = log_actions.add_parser("read", help="The independent reader's read of a rejection")
    read.add_argument("id", help="the candidate's neutral id, such as closure-01")
    read.add_argument("criterion", choices=READ_REQUIRED)
    read.add_argument("verdict", choices=("agree", "disagree"))
    read.add_argument("--resolution", help="required on a disagreement: his decision and why")

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
    repeats_parser = protocol_actions.add_parser(
        "repeats",
        help="Set the repeats from a finished pilot; writes repeats.json beside it, once",
    )
    repeats_parser.add_argument(
        "--pilot", required=True, metavar="SWEEP_ID", help="the pilot sweep's id"
    )
    repeats_parser.add_argument("--store", choices=("local", "s3"), default="s3")
    repeats_parser.add_argument("--bucket", default=None)
    repeats_parser.add_argument("--profile", default=None)

    records_parser = protocol_actions.add_parser(
        "records",
        help="The record checks over every pilot and official sweep; read-only; writes the evidence file",
    )
    records_parser.add_argument("--store", choices=("local", "s3"), default="s3")
    records_parser.add_argument("--bucket", default=None)
    records_parser.add_argument("--profile", default=None)

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
    "awareness": cmd_sweep_awareness,
    "refusals": cmd_sweep_refusals,
    "tokens": cmd_sweep_tokens,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.group == "dossier":
        return cmd_dossier(args)
    if args.group == "case":
        return cmd_case(args)
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
    if args.group == "analyze":
        try:
            return cmd_analyze(args)
        except (SweepRefusal, ExperimentError) as exc:
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
