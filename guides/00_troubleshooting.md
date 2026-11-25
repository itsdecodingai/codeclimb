# Troubleshooting

After this guide you can match a failure's error text to its cause and fix. Each entry: error text → cause → fix.

## Known failures

### `Cannot connect to the Docker daemon`

- **Cause:** Docker is not running. Every `harbor run`, `verifier/grade.sh` and `code_metrics.py` call needs it; the dry run and the unit tests do not.
- **Fix:** start Docker Desktop or the Docker Engine, then rerun the command.

### `run: python3 assemble.py <stack>`

- **Cause:** `verifier/grade.sh` found no `tasks/codeclimb-<stack>/tests/verifier/`. A task's `/app`, instruction and verifier copy are generated and gitignored.
- **Fix:** run `python3 assemble.py <stack>` ([02_running.md#assemble-a-task-and-check-a-job-file](02_running.md#assemble-a-task-and-check-a-job-file)). The same holds before any `harbor run -c job-configs/<stack>-*.yaml` on a fresh clone.

### `assemble <task> <stack> failed`

- **Cause:** `assemble.py maintenance` failed. On a fresh clone the usual cause is that the maintenance branches were never fetched, so it cannot read the task's commit.
- **Fix:** `git fetch origin main langchain 'refs/heads/benchmark-maint-*:refs/heads/benchmark-maint-*'`, then rerun. For any other cause, run `python3 assemble.py maintenance <task> <stack>` by hand to see its error.

### `export CLAUDE_CODE_OAUTH_TOKEN, CLAUDE_FORCE_OAUTH=1 and CODECLIMB_BENCH_LANGSMITH_API_KEY first`

- **Cause:** `job-configs/run-all.sh` or `job-configs/pilot.sh` was started without the subscription token exported, or `.env` has no `LANGSMITH_API_KEY`.
- **Fix:** use `./start-full-run.sh`, which exports the token from `.env`, or export both variables as in [02_running.md#one-job](02_running.md#one-job). Add `LANGSMITH_API_KEY` to `.env` ([01_setup.md#environment-variables](01_setup.md#environment-variables)).

### `unset ANTHROPIC_API_KEY: trials run on the subscription, never a provider key`

- **Cause:** `ANTHROPIC_API_KEY` is exported in the shell. Harbor's `claude-code` agent prefers an API key over the subscription token.
- **Fix:** `unset ANTHROPIC_API_KEY`. Keep the key in `.env` only, where `job-configs/pi-auth.py anthropic` reads it for the verifier's real tier.

### `no token in .env` or `no CLAUDE_CODE_OAUTH_TOKEN in .env`

- **Cause:** `start-full-run.sh` or a probe script found no `CLAUDE_CODE_OAUTH_TOKEN=` line in `.env`.
- **Fix:** run `claude setup-token` and add the token to `.env` on one line.

### `401 OAuth access token is invalid` (the trial records `UnknownApiError`)

- **Cause:** `claude setup-token` prints the 108-character token wrapped over two lines, and only the first line was copied.
- **Fix:** join both lines into one value in `.env`.

### `export CODECLIMB_BENCH_PI_AUTH="$(python3 job-configs/pi-auth.py)" first, or set CODECLIMB_VERIFIER_FAMILIES without real`

- **Cause:** `run-all.sh` runs the `real` family by default and found no Pi login for the verifier.
- **Fix:** `export CODECLIMB_BENCH_PI_AUTH="$(python3 job-configs/pi-auth.py anthropic)"` with `ANTHROPIC_API_KEY` in `.env`, or run with `CODECLIMB_VERIFIER_FAMILIES=basic,hidden`.

### `no ANTHROPIC_API_KEY in the environment or .env`

- **Cause:** `job-configs/pi-auth.py anthropic` found no key.
- **Fix:** add `ANTHROPIC_API_KEY` to `.env`.

### `<path>: no github-copilot login; run npx pi, then /login github-copilot`

- **Cause:** `job-configs/pi-auth.py` without an argument reads the Copilot login from `~/.pi/agent/auth.json`, and there is none.
- **Fix:** log Pi in to Copilot as the message says, or use `pi-auth.py anthropic`.

### `reference grades failed: no trial started; see jobs/all-<stamp>-logs`

- **Cause:** a reference grade has no reward, or a build pin is below reward 1. A harness is never graded on a check its pin fails, so the run stops before any trial.
- **Fix:** read `jobs/all-<stamp>-logs/reference-<stack>-<commit>.log` and the lines `run-all.sh` printed per grade (`BAD <stack> <commit> reward ... failed: ...`). Fix the cause and rerun. `CODECLIMB_IGNORE_REFERENCES=1` starts the trials anyway; use it only when the failed check is a known flake.

### `stopped on a usage limit in: ...`

- **Cause:** the subscription's usage limit stopped a trial. `usage_watch.py` then stopped every running job with SIGTERM, keeping each trial's `/app` and sessions, and no new job started.
- **Fix:** wait for the limit to reset, then continue ([02_running.md#continue-a-stopped-run](02_running.md#continue-a-stopped-run)).

### `CODECLIMB_CONTINUE: no job folder jobs/all-<stamp>-*`

- **Cause:** the value is not the prefix of a stopped run's job folders.
- **Fix:** pass the prefix without the job name, for example `jobs/all-20261120-1102`.

### The LangChain Agent Server exits with code 3, and `services-up` fails

- **Cause:** an EU LangSmith key with no endpoint: the default endpoint is the US one.
- **Fix:** add `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com` to `.env`.

### `collection failed in the source trial`

- **Cause:** `harbor trial regrade` refuses a trial whose artifacts were not all collected. A `nop` trial started by hand leaves no `/logs/agent/sessions/projects`.
- **Fix:** grade reference builds and maintenance floors through `job-configs/reference.sh` and `job-configs/maintenance.sh`: their compose overlays create the empty sessions folder.

### A trial's reward is far below what the harness reported, with `typecheck` and every night failing

- **Cause:** `/app` arrived half-copied in the verifier. `analyze.py` reads `artifacts/manifest.json` and counts such a trial as infra, in no mean.
- **Fix:** check `artifacts/manifest.json` in the trial folder. `task.toml` already excludes `.venv`, whose absolute symlink aborted the copy in the pilot; a new exclude belongs there.

### `VerifierTimeoutError` and no reward

- **Cause:** Harbor collects nothing from a verifier it timed out. The verifier keeps its own deadline of 19800 s, below Harbor's 21600 s, so this shows only if a task's `[verifier] timeout_sec` was lowered.
- **Fix:** keep `timeout_sec = 21600` in `tasks/codeclimb-<stack>/task.toml`; `verifier/families_test.py` checks the deadline against every task's limit.

## FAQ

**Does a trial need a model provider key?** No. The harness runs on the Claude subscription, and every night the reward counts runs with `--mock`. Only the verifier's `real` family calls a provider, with a key the harness never sees.

**Why is no CodeClimb build in this branch?** A build would hand the harness the answer. Builds exist only as trial artifacts under `jobs/`, and the reference builds stay on `main` and `langchain`, named here by commit SHA ([docs/adr/0002](../docs/adr/0002-self-contained-branch-with-vendored-inputs.md)).

**Why does a rerun give other numbers?** A harness is not deterministic. A rerun reproduces the protocol and the conditions; per-trial numbers differ ([docs/results/reproduce.md](../docs/results/reproduce.md)).

**Why is a trial listed as a leak although its reward is 1?** The leak scan found a blocked host or the repo owner in what the harness did. The trial keeps its reward and is reported apart; the operator reads the hits and may clear it by hand ([02_running.md#analysis](02_running.md#analysis)).

**Why did a trial's reward change after the run?** The regrade rule: a trial that did not pass is regraded once from its recorded artifacts, and the regrade counts ([02_running.md#regrade](02_running.md#regrade)).

**Where are the `npm run` commands?** On the reference builds' branches. Nothing on this branch serves CodeClimb; the given `.claude/skills/codeclimb-e2e` skill describes the LangChain reference build.

Back to the index: [../README.md#guides](../README.md#guides)
