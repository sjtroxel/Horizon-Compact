# Horizon Compact: the single entry point for routine tasks.
# `make help` lists targets. `make check` is what CI runs, except the one check CI skips by name.

.DEFAULT_GOAL := help
.PHONY: help setup install fmt lint typecheck test root-check paths-check doctor check \
        guard-history fingerprint tf-fmt tf-check

GUARD := uv run --no-sync python -m horizon_compact.privacy.guard
ROOT_CAP := 16
TF_BOOTSTRAP := infra/terraform/bootstrap
TF_MAIN := infra/terraform/main

help: ## List available targets
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[1m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Create the venv and install all dependencies (uv provisions Python 3.13)
	@command -v uv >/dev/null || { echo "uv is not installed: https://docs.astral.sh/uv/"; exit 1; }
	uv sync --locked

# The term file's path is stored in this clone's own git config (.git/config), which git never tracks,
# so the path cannot be committed by mistake (Phase 0, decision 2). It is asked for once per clone.
setup: install ## One-time setup per clone: term-file path, all three hook types, then doctor
	@if [ -z "$$HC_NAME_GUARD_TERMS" ] && [ -z "$$(git config --local --get hc.nameGuardTerms)" ]; then \
		printf 'Path to the private name-guard term file: '; read -r path; \
		[ -f "$$path" ] || { echo "No such file. Nothing was stored."; exit 1; }; \
		git config --local hc.nameGuardTerms "$$path"; \
		echo "Stored in .git/config (never tracked)."; \
	fi
	uv run --no-sync pre-commit install
	@$(GUARD) doctor

fmt: ## Format and auto-fix the code
	uv run --no-sync ruff format src tests
	uv run --no-sync ruff check --fix src tests

lint: ## Check formatting and lint without modifying anything
	uv run --no-sync ruff format --check src tests
	uv run --no-sync ruff check src tests

typecheck: ## Run mypy (strict)
	uv run --no-sync mypy

test: ## Run the test suite
	uv run --no-sync pytest

# Counts tracked AND untracked-but-not-ignored paths, so the cap holds before a commit, not only after.
root-check: ## Fail if the repo root has grown past its cap
	@files=$$(git ls-files --cached --others --exclude-standard); \
	count=$$(echo "$$files" | awk -F/ 'NF==1' | sort -u | wc -l); \
	dirs=$$(echo "$$files" | awk -F/ 'NF>1 {print $$1}' | sort -u | wc -l); \
	total=$$((count + dirs)); \
	echo "repo root: $$count files + $$dirs dirs = $$total entries (cap $(ROOT_CAP))"; \
	[ "$$total" -le $(ROOT_CAP) ] || { echo "Root cap exceeded: relocate something before raising the cap."; exit 1; }

# No target runs plan, apply, import or destroy: anything that authenticates is typed by hand (Phase 0.5, decision 6).
tf-fmt: ## Rewrite Terraform files into canonical format
	terraform -chdir=$(TF_BOOTSTRAP) fmt -recursive
	terraform -chdir=$(TF_MAIN) fmt -recursive

# Needs no credentials and makes no AWS call. `init` only downloads the provider; -lockfile=readonly fails if
# the committed .terraform.lock.hcl disagrees with the configuration instead of resolving something new.
tf-check: ## Terraform fmt -check and validate (no credentials, no AWS call)
	terraform -chdir=$(TF_BOOTSTRAP) fmt -check -recursive
	terraform -chdir=$(TF_BOOTSTRAP) init -backend=false -input=false -lockfile=readonly
	terraform -chdir=$(TF_BOOTSTRAP) validate
	terraform -chdir=$(TF_MAIN) fmt -check -recursive
	terraform -chdir=$(TF_MAIN) init -backend=false -input=false -lockfile=readonly
	terraform -chdir=$(TF_MAIN) validate

paths-check: ## Fail if any tracked path is under methods-appendix/ (needs no private file)
	@$(GUARD) paths-check

doctor: ## Check the hooks are installed and the private term file loads
	@$(GUARD) doctor

# CI never has the hooks or the private term file, so `doctor` is skipped there BY NAME, and says so.
# Everything else is identical, so a green local `make check` predicts a green check on GitHub.
check: lint typecheck test root-check paths-check tf-check ## Everything CI runs, plus doctor when not in CI
ifdef CI
	@echo "SKIPPED in CI: doctor (no hooks or private term file on a CI runner, by design)"
else
	@$(GUARD) doctor
endif

guard-history: ## Scan every commit, branch, tag and tag message with the name guard
	@$(GUARD) history

fingerprint: ## Print the longlist's current SHA-256, for updating the private term file
	@$(GUARD) fingerprint
