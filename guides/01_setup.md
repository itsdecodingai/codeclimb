# Setup

After this guide `DRY=1 job-configs/run-all.sh 3` assembles every task and prints `ok` for each of the 30 jobs, and `.env` holds the keys a paid run needs.

The benchmark measures a harness (a coding agent, here Claude Code) building CodeClimb from a build spec on two stacks, [Inngest](https://inngest.link/dai-gh) and LangChain. Words such as trial, arm and verifier are defined in [GLOSSARY.md](../GLOSSARY.md).

## Prerequisites

| Tool | Min version | Purpose | Install |
|---|---|---|---|
| Docker | Desktop or Engine, running (measured on Docker Desktop 29.4.3, arm64) | Every trial and every verifier run starts its own `docker:27-dind` sidecar; also the task images and the analysis container | [docker.com](https://docs.docker.com/get-docker/) |
| uv | any | Installs Harbor and runs `analyze.py` | [install](https://docs.astral.sh/uv/) |
| Harbor | 0.25.0 exactly | Runs trials | `uv tool install harbor==0.25.0` |
| Python 3 | 3.x on the host | `assemble.py`, `regrade.py`, `code_metrics.py`, `gate.py`, the unit tests; standard library only | [python.org](https://www.python.org) |
| git | any | Reads the reference builds and maintenance commits with `git archive` | [git-scm.com](https://git-scm.com) |
| Claude Code CLI | any, on the host | Only for `claude setup-token`. Trial images carry their own pinned 2.1.322 | [install](https://docs.claude.com/en/docs/claude-code/setup) |
| macOS `caffeinate` | ships with macOS | Only `start-full-run.sh` uses it. On Linux run `job-configs/run-all.sh` yourself ([02_running.md#full-run](02_running.md#full-run)) | none |

Each trial container gets 6 CPUs, 6144 MB of memory and 10 GB of storage (`tasks/codeclimb-<stack>/task.toml`), plus its sidecar. The full run keeps 3 jobs going at once, so leave room for 3 of these.

## Install

```bash
git clone -b benchmark https://github.com/itsdecodingai/codeclimb.git codeclimb-benchmark
cd codeclimb-benchmark
uv tool install harbor==0.25.0
git fetch origin main langchain 'refs/heads/benchmark-maint-*:refs/heads/benchmark-maint-*'
```

The fetch brings the reference builds (`main`, `langchain`) and the 20 maintenance task branches. Nothing is checked out from them: `job-configs/reference.sh` and `assemble.py maintenance` read their commits with `git archive`.

Check the install:

```bash
harbor --version
```

Prints `0.25.0`.

```bash
DRY=1 job-configs/run-all.sh 3
```

Prints `slots: 3; order: ...` and then one `ok <job>, 3 attempts` line for each of the 30 jobs. It needs no key and no Docker daemon, and takes under a minute.

## Environment variables

There is no `.env.example` on this branch. Create `.env` at the repo root (gitignored) with the keys below.

| Variable | Required | Source | Read by |
|---|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | For any trial with a real harness | `claude setup-token`, on a Claude subscription. The command prints the token wrapped over two lines: join both | `start-full-run.sh`, `job-configs/probes/run.sh` read it from `.env`; every other run script expects it exported |
| `LANGSMITH_API_KEY` | For every LangChain task, the `nop` one included | [smith.langchain.com](https://smith.langchain.com) → Settings → API keys | `job-configs/bench-env.sh`, sourced by every run script and `verifier/grade.sh` |
| `LANGSMITH_ENDPOINT` | Only with an EU key: `https://eu.api.smith.langchain.com` | Your LangSmith region | `job-configs/bench-env.sh` |
| `ANTHROPIC_API_KEY` | Only for the verifier's real tier on the Claude API | [console.anthropic.com](https://console.anthropic.com) | `job-configs/pi-auth.py anthropic`. Keep it in `.env`, never exported |

> [!WARNING]
> Never export `ANTHROPIC_API_KEY` in the shell that starts trials: Harbor prefers an API key over the subscription token, and `job-configs/run-all.sh` refuses to start while it is set.

Shell variables, set per command:

| Variable | Required | What it does | Read by |
|---|---|---|---|
| `CLAUDE_FORCE_OAUTH=1` | With `CLAUDE_CODE_OAUTH_TOKEN`, for any harness trial | Makes Claude Code use the subscription token | Harbor's `claude-code` agent; checked by `run-all.sh`, `pilot.sh` |
| `CODECLIMB_BENCH_PI_AUTH` | For the `real` family | The Pi login handed to the verifier alone: `"$(python3 job-configs/pi-auth.py anthropic)"`, or without the argument for a GitHub Copilot login | `run-all.sh`, the tasks' `tests/docker-compose.yaml` |
| `CODECLIMB_PI_AUTH_PATH` | No | Another Pi `auth.json` than `~/.pi/agent/auth.json` for the Copilot login | `job-configs/pi-auth.py` |
| `CODECLIMB_REAL_PROVIDER` | No | `copilot` puts the real tier on the Copilot login instead of the Claude API | `start-full-run.sh` |
| `CODECLIMB_VERIFIER_FAMILIES` | No | Which check families the verifier runs: `basic`, `hidden`, `real`, comma-separated. Default all | `verifier/families.py`, `run-all.sh` |
| `CODECLIMB_VERIFIER_ONLY` | No | Runs only the named hidden or real tests, comma-separated | `verifier/families.py` |
| `CODECLIMB_VERIFIER_KEEP` | No | A folder: the hidden durability tests copy each faulted night's folder and the service logs there | `verifier/durability_tests.py` |
| `CODECLIMB_CONTINUE` | No | The `jobs/all-<stamp>` prefixes of stopped runs to continue | `run-all.sh` |
| `CODECLIMB_IGNORE_REFERENCES` | No | `1` starts the trials although a reference grade failed | `run-all.sh` |
| `CODECLIMB_JOBS_DIR` | No | Output folder of `reference.sh` (default `jobs`) | `job-configs/reference.sh` |
| `CODECLIMB_BENCH_LANGSMITH_API_KEY`, `CODECLIMB_BENCH_LANGSMITH_ENDPOINT` | No | Override the two LangSmith values of `.env` | `job-configs/bench-env.sh`, the tasks' compose files |
| `DRY` | No | `1` makes `run-all.sh` and `pilot.sh` assemble and check each job, with no trial | `run-all.sh`, `pilot.sh` |
| `STACK` | No | The stack a probe runs on: `inngest` (default) or `langchain` | `job-configs/probes/run.sh` |
| `PILE` | No | Another pile of build tickets for a `pocock` job | `job-configs/pocock.sh` |

Set by the scripts themselves, never by you: `CODECLIMB_ASSEMBLED`, `CODECLIMB_POCOCK_DIR`, `CODECLIMB_REFERENCE_DIR` (the run scripts), and `CODECLIMB_PROXY_HOST`, `CODECLIMB_BACKSTOP_S`, `CODECLIMB_PAUSE_TIMEOUT_S`, `CODECLIMB_MOCK_CREDIT` (the task environments and the verifier, for the build under test).

## External services

### Claude subscription

The harness under test, Claude Code on Opus 5.5 at medium effort, runs on a Claude subscription, never on an API key. Paid plan; run `claude setup-token` and sign in. Fills `CLAUDE_CODE_OAUTH_TOKEN`. When a trial hits the plan's usage limit, `usage_watch.py` stops the run and keeps every trial's state ([02_running.md#continue-a-stopped-run](02_running.md#continue-a-stopped-run)).

### LangSmith

The LangChain build's Agent Server exits without a LangSmith key, and the `mcp-docs` and `full` arms use the LangSmith MCP server. Free tier; sign up at [smith.langchain.com](https://smith.langchain.com) and [create an API key](https://docs.langchain.com/langsmith/create-account-api-key). Fills `LANGSMITH_API_KEY` and, for an EU workspace, `LANGSMITH_ENDPOINT`. The key is written into each trial's `/app/.env` with tracing off.

### Claude API

Only the verifier's `real` family uses it: small real-model nights with CodeClimb's coder and reviewer on Claude Haiku. Paid; create a key at [console.anthropic.com](https://console.anthropic.com). Fills `ANTHROPIC_API_KEY`. The harness never sees the key. Without it, run with `CODECLIMB_VERIFIER_FAMILIES=basic,hidden`.

## Cost

Trial cost is Claude Code's own estimate at API prices, on the subscription. The figures are from the 2026-11-20 run ([docs/results/metrics.md](../docs/results/metrics.md)).

| Run path | Cost | Needs |
|---|---|---|
| Free checks: unit tests, dry run, `--print-config`, topology check, `nop` floor | $0 | Docker for the last two |
| Grade a reference build, `basic` and `hidden` families | $0 | Docker; LangSmith key on LangChain |
| Grade a reference build with the `real` family | A few Haiku nights on the Claude API; measured at about $0.31 to $0.38 per run on Copilot, not measured on the Claude API | `CODECLIMB_BENCH_PI_AUTH` |
| A probe | $0.06 to $0.38 each; the `pocock` smoke trial $0.61, capped at $3 | Subscription token |
| One maintenance trial | $0.16 to $3.41, mean $0.85 | Subscription token |
| One one-shot build trial | About $12 to $15, capped at $32 | Subscription token |
| One `pocock` build trial | About $29 to $31, capped at $32 | Subscription token |
| The full run, 90 trials | $562 in the 2026-11-20 run, which took 5 days with its stops | All keys above |

Next: [02_running.md](02_running.md)
