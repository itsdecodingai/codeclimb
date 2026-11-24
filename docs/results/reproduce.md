# Reproducing the full run

How to rerun the benchmark behind [metrics.md](metrics.md), with the same harness, model, tasks, verifier and analysis. A coding agent is not deterministic, so a rerun reproduces the protocol and the conditions; per-trial numbers will differ. The second half records how the 2026-11-20 to 2026-11-24 run actually went, including every step that departed from a single clean run.

## What is fixed

| | value |
|---|---|
| benchmark code | branch `benchmark`, the commit that adds this file |
| Harbor | 0.25.0 (`uv tool install harbor==0.25.0`) |
| harness | Claude Code 2.1.322, `anthropic/claude-opus-5-5`, `reasoning_effort: medium`, on the operator's subscription (OAuth token, never an API key) |
| job files | `job-configs/<stack>-<arm>.yaml`; `n_attempts: 3`, one trial at a time per job, `max_retries: 1`, a budget cap per trial (`max_budget_usd`) |
| build pins (reference builds) | Inngest `5a81c07` (on `main`), LangChain `3612892` (on `langchain`): `assemble.BUILD_PINS` |
| maintenance tasks | `maintenance.COUNTED`: r14, r3, r10, r15, r2, r12, c7, c2, c4, c6, on the `benchmark-maint-*` branches; bases Inngest `1360cb4`, `1452a93`, `bcabd72`, LangChain `400bd40`, `9911231`, `9d04590` |
| verifier families | builds: `basic,hidden,real`; maintenance: `basic,hidden` (`maintenance.FAMILIES`) |
| real tier | coder and reviewer on Claude Haiku through the Claude API (`pi-auth.py anthropic`) |
| given inputs | `configs/`, `scenarios/`, `docker/`, `specs/<stack>/`: the run's build specs hash to `spec_sha256` Inngest `2b117c49f900…`, LangChain `4d5984624921…` (see `trials.jsonl`) |

## Prerequisites

- macOS or Linux with Docker running. Every trial and verifier run starts its own `docker:27-dind` sidecar, so leave room for 3 at a time.
- `uv`, Python 3, Harbor 0.25.0.
- The reference and maintenance commits present locally: `reference.sh` and the maintenance assembly read them with `git archive`.

```bash
git fetch origin main langchain 'refs/heads/benchmark-maint-*:refs/heads/benchmark-maint-*'
```

- A `.env` at the repo root (gitignored) with:
  - `CLAUDE_CODE_OAUTH_TOKEN`: the subscription token the harness runs on (`claude setup-token`).
  - `LANGSMITH_API_KEY` (and `LANGSMITH_ENDPOINT` for the EU region): the LangChain trials' LangSmith MCP and tracing.
  - `ANTHROPIC_API_KEY`: used only by the verifier's real tier. The harness never sees it, and `run-all.sh` refuses to start if it is exported.

## Free checks first

```bash
DRY=1 job-configs/run-all.sh 3
```

```bash
harbor run -p tasks/codeclimb-inngest -a nop
```

```bash
harbor run -p tasks/codeclimb-langchain -a nop
```

The dry run assembles every task, prints the job order and checks each job file with `--print-config`. The two `nop` runs check the task images and the verifier for $0.

## The run

One command runs the whole benchmark: `start-full-run.sh` reads the token from `.env`, sets the real tier to the Claude API and starts `job-configs/run-all.sh 3` under `caffeinate`.

```bash
./start-full-run.sh
```

What it does (`job-configs/run-all.sh`, docs/codeclimb-eval-spec.md "Jobs, repeats, cost"):

1. **Reference grades ($0).** Both build pins and the 6 maintenance bases are graded by the current verifier (`job-configs/reference.sh`). The trials start only if every grade has a reward and each pin reaches reward 1. A harness is never graded on a check its pin fails.
2. **Trials (subscription).** It runs 30 jobs of 3 attempts each, 90 trials, with at most 3 jobs at a time:
   - 10 build jobs: 2 stacks x `bare`, `skills`, `mcp-docs`, `full`, plus `full` x pocock;
   - 20 maintenance jobs: 2 stacks x 10 tasks, arm `bare`.
   The pocock jobs start first; the rest follow in shuffled order, one minute apart. On the first usage-limit stop, `usage_watch.py` stops every running job with SIGTERM, keeping its state, and no new job starts. A run stopped by hand (SIGTERM) continues the same way.
3. **Regrades ($0).** Every trial that did not pass is regraded once from its recorded artifacts, and the regrade counts (`regrade.py`). Then `code_metrics.py` measures every build trial against its stack's pin.

Output goes to `jobs/all-<stamp>-*/`, and the script prints the `analyze.py` command at the end.

**After a stop** (usage limit or by hand), continue once the limit resets or the fix is in. Each job runs only the attempts it still lacks, and the reference grades are reused:

```bash
CODECLIMB_CONTINUE="jobs/all-<stamp>" ./start-full-run.sh
```

## Leak review

`analyze.py` keeps any trial the leak scan flags out of every mean. Read each flagged trial's hits by hand and, if the operator clears it, add it with the reason to `LEAK_CLEARED` in `analyze.py` and to the spec's "cleared by hand" list. Rerun one trial of the cell for each leak that stays (see below).

## Analysis

```bash
uv run python analyze.py jobs/all-<stamp>-*-* jobs/all-<stamp>-references jobs/all-<stamp>-regrades > jobs/report.txt
```

The first folder gets `trials.jsonl`, one row per trial; the report is what [metrics.md](metrics.md) is built from. The per-cell code-quality table in metrics.md is the mean of each counted row's `code_metrics` in `trials.jsonl`.

## How the 2026-11-20 run actually went

Each step below is in the job folders and in the git history.

| stamp | what |
|---|---|
| `all-20261120-1102` | first `run-all.sh`, at `630c2a6`. It graded the references and ran maintenance c6, r10, r12, r14 and r15 on both stacks, plus LangChain c4. Its build trials were deleted later (see `all-20261122-1520`). It was stopped. |
| `all-20261121-1146` | continued, with the changes committed as `33e1509`: the verifier deadline, the time per real night, and a fake Pi login in the build containers. It made fresh reference grades, which every later step reused, and ran pocock on both stacks, c7 and Inngest r14. It was stopped. |
| `all-20261122-1002` | continued at `0c39713`, which lets one run continue several stopped ones. It ran Inngest pocock's third attempt, c4 and r3. It was stopped. |
| `all-20261122-1520` | continued. It ran every one-shot build job (only 2 attempts for LangChain `mcp-docs`, which kept 1 trial from `all-20261121-1146`), c2 and r2, then the regrades and the code metrics. Before it started, the other one-shot build trials from earlier stamps were deleted, because the fake Pi login change outdated them. |
| `regrades-anthropic-20261122` | the Copilot quota for the real tier ran out on 2026-11-22. From then on the real tier ran on the Claude API, and two Inngest pocock trials graded before the switch were regraded on it ($0, `harbor trial regrade`) |
| `all-20261123-2114` | one extra LangChain one-shot `full` trial (`o8xG5nj`), because `U3NPDfX` is a leak and the cell had n=2; then its regrade check and code metrics |

**Rule changes during the run** (each one went into the spec first, then the code):
- **2026-11-23:** the leak scan counts a file byte-identical to a given file as given at any path. The hand-cleared list was added; `gVLNHRW` was cleared and `U3NPDfX` kept as a leak.
- **2026-11-23:** code metrics leave out files the build's own git ignores. All 30 earlier build trials were re-measured on 2026-11-24, with the old files kept as `code-metrics.old.json`.
- **2026-11-24:** the hand-cleared rule allows a request to a third party's page on a blocked host; `o8xG5nj` was cleared under it.

The extra trial ran this way (from the repo root, the same environment as `start-full-run.sh`):

```bash
python3 assemble.py langchain && harbor run -c job-configs/langchain-full.yaml -k 1 --job-name all-<stamp>-langchain-full -o jobs -y
```

```bash
python3 regrade.py jobs/all-<stamp>-regrades --slots 1 jobs/all-<stamp>-langchain-full
```

```bash
python3 code_metrics.py jobs jobs/all-<stamp>-langchain-full
```

The final report was produced by:

```bash
uv run python analyze.py jobs/all-20261120-1102-*-* jobs/all-20261121-1146-*-* jobs/all-20261122-1002-*-* jobs/all-20261122-1520-*-* jobs/all-20261123-*-langchain-full jobs/all-20261121-1146-references jobs/all-20261122-1520-regrades jobs/regrades-anthropic-20261122 jobs/all-20261123-2114-regrades > jobs/report-final-20261124.txt
```


Run in one go from the commit that adds this file, the same steps reduce to `./start-full-run.sh`, any continues, the leak review and the analysis.
