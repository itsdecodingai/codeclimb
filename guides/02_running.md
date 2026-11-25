# Running

After this guide you can run every part of the benchmark: the free checks, a reference grade, one job, the full run, its regrades and the analysis that produces [docs/results/metrics.md](../docs/results/metrics.md).

Scenarios follow the order the benchmark runs in. Everything up to [Probes](#probes) costs $0. From there on a command uses the operator's Claude subscription: start one only with a go-ahead for that run. Setup: [01_setup.md](01_setup.md). The stacks are [Inngest](https://inngest.link/dai-gh) and LangChain; `<stack>` below is `inngest` or `langchain`.

## Unit tests

Needs: [01_setup.md#install](01_setup.md#install). No Docker, no key.

```bash
python3 -m unittest analyze_test assemble_test regrade_test gate_test usage_watch_test
```

Prints `Ran 95 tests` and `OK` (measured at `944d993`, 9 s).

```bash
(cd verifier && python3 -m unittest discover -p '*_test.py')
```

Prints `Ran 112 tests` and `OK`.

`code_metrics_test.py` builds and runs the analysis container, so it needs Docker:

```bash
python3 -m unittest code_metrics_test
```

Entry points: the `*_test.py` file beside each module, and `verifier/*_test.py`.

## Dry run

Needs: [01_setup.md#install](01_setup.md#install), including the `git fetch` of the reference refs.

```bash
DRY=1 job-configs/run-all.sh 3
```

Assembles both build tasks and the 20 maintenance tasks, prints `slots: 3; order: ...` with the shuffled job order, then `ok <job>, 3 attempts` for each of the 30 jobs (measured at `944d993`, 32 s). `bad <job>` names a job file Harbor rejects.

Entry point: `job-configs/run-all.sh`.

## Assemble a task and check a job file

A task's `/app`, its instruction and its copy of the verifier are generated, never committed. Assemble before any `harbor run` on that task.

```bash
python3 assemble.py inngest
```

```bash
python3 assemble.py langchain
```

Each writes `tasks/codeclimb-<stack>/environment/app/` (the given inputs, `SPEC.md`, `E2E.md`), `instruction.md`, `tests/verifier/` and `assembled.json` with the sha256 of the build spec and of the given inputs. It fails, naming the string and the file, when the output would tell the harness where it is.

A maintenance task, for example repair `r14` on LangChain:

```bash
python3 assemble.py maintenance r14 langchain
```

Writes `tasks/codeclimb-langchain-r14/`. The task ids are `maintenance.COUNTED`: `r14`, `r3`, `r10`, `r15`, `r2`, `r12`, `c7`, `c2`, `c4`, `c6`.

Check a job file against Harbor's schema:

```bash
harbor run -c job-configs/inngest-full.yaml --print-config
```

Prints the resolved job config and starts nothing. The job files are `job-configs/<stack>-{bare,skills,mcp-docs,full,full-pocock,nop}.yaml`.

Entry points: `assemble.py`, `maintenance.py` (the task registry).

## Topology check

Needs: Docker running. Proves inside Harbor that a trial and its verifier each get a working Docker daemon, a shared `/app` and the GitHub block ([docs/adr/0001](../docs/adr/0001-trial-container-shares-the-sidecar-network.md)).

```bash
tasks/topology-check/run.sh
```

Harbor's `oracle` agent runs the probes; the reward is 1 when 18 of 18 checks pass (measured 2026-11-12, twice).

Entry point: `tasks/topology-check/`, `job-configs/topology-check.yaml`.

## Floor

Needs: Docker running, [the task assembled](#assemble-a-task-and-check-a-job-file); on LangChain also `LANGSMITH_API_KEY` in `.env`. A plain `harbor run` does not read `.env`, so the LangChain command sources `job-configs/bench-env.sh` first.

Harbor's `nop` agent leaves the given inputs as they are and the verifier grades them. The reward is the floor every cell is read against.

```bash
CODECLIMB_VERIFIER_FAMILIES=basic harbor run -c job-configs/inngest-nop.yaml -y
```

```bash
. job-configs/bench-env.sh && CODECLIMB_VERIFIER_FAMILIES=basic harbor run -c job-configs/langchain-nop.yaml -y
```

Measured 2026-11-13, with the task image built: Inngest reward 0.029 (1 of 34, `install`) in 1m 58s; LangChain 0.088 (3 of 34: `install`, `typecheck`, `image`) in about 16 min, most of it the wait for a server that never comes up. No night check passes on either. The reward is in `jobs/<job>/<trial>/verifier/reward.json`. `-y` answers Harbor's confirmation prompts.

AGENTS.md's form, `harbor run -p tasks/codeclimb-<stack> -a nop`, runs the same trial with every verifier family.

Entry point: `verifier/run.py` (`CHECKS` lists the 34).

## Grade a reference build

Needs: Docker running, the reference refs fetched; on LangChain `LANGSMITH_API_KEY` in `.env`. $0 with the `basic` and `hidden` families.

A reference build is graded before any trial: a harness is never graded on a check its reference build fails. Inside Harbor, where trials are graded:

```bash
CODECLIMB_VERIFIER_FAMILIES=basic,hidden job-configs/reference.sh inngest
```

```bash
CODECLIMB_VERIFIER_FAMILIES=basic,hidden job-configs/reference.sh langchain
```

Each exports the stack's pin (Inngest `5a81c07`, LangChain `3612892`) with `git archive` to `jobs/reference-<stack>-<commit>/` and runs the `nop` agent on it. Expect reward 1.0 (34 of 34). With `basic` alone the verifier takes about 7 min (measured 2026-11-13); with all three families it took 54 and 68 min in the full run. Pass another commit as the second argument to grade a maintenance base.

From the host, outside Harbor, on any build directory, with [the stack's task assembled](#assemble-a-task-and-check-a-job-file):

```bash
mkdir -p jobs/ref-inngest && git archive 5a81c07 | tar -x -C jobs/ref-inngest
```

```bash
verifier/grade.sh jobs/ref-inngest inngest
```

Prints `reward: jobs/grade-inngest-<time>/reward.json`; `checks.json` beside it holds each check's output tail.

To add the `real` family, export `CODECLIMB_BENCH_PI_AUTH` first ([01_setup.md#environment-variables](01_setup.md#environment-variables)) and drop the `CODECLIMB_VERIFIER_FAMILIES` prefix. That spends on the Claude API or the Copilot login and needs a go-ahead.

Entry points: `job-configs/reference.sh`, `verifier/grade.sh`, `verifier/run.py`.

## Probes

Needs: `CLAUDE_CODE_OAUTH_TOKEN` in `.env`, Docker running. Uses the subscription: $0.06 to $0.38 per probe.

Short trials in a stack's trial environment, with the instruction replaced by a probe template and no verifier:

```bash
job-configs/probes/run.sh one-line
```

```bash
STACK=langchain job-configs/probes/run.sh blocklist
```

Probes: `one-line`, `network`, `search`, `budget`, `big`, `blocklist`. The two smoke scripts below cost up to $0.15 per arm and $0.61 for the `pocock` one. Output: `jobs/probe-<probe>-<stack>-<time>/`. The `blocklist` probe must report that `curl https://github.com` fails and a `WebFetch` of the repo is denied, while `www.inngest.com/llms.txt` and `docs.langchain.com/llms.txt` load.

One short trial per arm, to see that the arm's skills and MCP servers reach the harness:

```bash
job-configs/probes/arm-smoke.sh inngest bare skills mcp-docs full
```

The `pocock` workflow on a dummy pile of four build tickets, capped at $3:

```bash
job-configs/probes/pocock-smoke.sh inngest
```

Entry point: `job-configs/probes/`.

## One job

Needs: [Grade a reference build](#grade-a-reference-build) at reward 1.0 on that stack, the task assembled, and the token exported:

```bash
unset ANTHROPIC_API_KEY; export CLAUDE_FORCE_OAUTH=1 CLAUDE_CODE_OAUTH_TOKEN="$(grep '^CLAUDE_CODE_OAUTH_TOKEN=' .env | cut -d= -f2-)"
```

```bash
. job-configs/bench-env.sh
```

The second line exports the LangSmith key from `.env` for a LangChain job; a plain `harbor run` has no guard against an exported `ANTHROPIC_API_KEY`, which Harbor would prefer over the subscription.

A job is one cell: one stack, one arm, 3 trials one after another. Uses the subscription: about $12 to $15 per one-shot trial, capped at $32.

```bash
harbor run -c job-configs/inngest-bare.yaml -o jobs -y
```

Add `-k 1` for one trial instead of 3. Harbor prints a summary with the mean reward; each trial's folder under `jobs/inngest-bare/` holds `result.json`, `verifier/reward.json`, `artifacts/app/` (the build) and `agent/` (the trajectory). A one-shot trial's harness phase took 46 to 83 min in the 2026-11-20 run; the verifier adds about an hour with all three families.

The `full × pocock` job needs its pile of build tickets copied into the trial, so it has its own script:

```bash
job-configs/pocock.sh inngest -o jobs -y
```

Entry points: `job-configs/<stack>-<arm>.yaml`, `job-configs/pocock.sh`, `context/` (what each arm adds).

## Maintenance tasks

Needs: the reference refs fetched. A maintenance task starts from a reference build and asks for one change or one repair.

The floor of a task, $0: its `/app` as given, graded with the `nop` agent. Its target tests must fail.

```bash
job-configs/maintenance.sh r14 inngest
```

The gate, $0: 3 reference runs on the base and 3 on the task commit, per stack, then the verdict. The commits and target tests of each task are in `maintenance.py`.

```bash
CODECLIMB_VERIFIER_FAMILIES=hidden CODECLIMB_VERIFIER_ONLY=<targets> job-configs/reference.sh <stack> <sha> -k 3
```

```bash
python3 gate.py r14 jobs
```

Prints the verdict as JSON: `pass` or `fail` with the reasons, and per stack the failing set and the fix size.

A pilot, on the subscription: one trial per stack of each named task, `bare` arm, `basic` and `hidden` families. Needs the token exported as in [One job](#one-job).

```bash
job-configs/pilot.sh r14 c6
```

Writes `jobs/pilot-<task>-<stack>-<stamp>/` and prints `<job> exit 0` per job. `DRY=1 job-configs/pilot.sh r14 c6` checks the job files only.

Entry points: `job-configs/maintenance.sh`, `gate.py`, `job-configs/pilot.sh`, `maintenance.py`.

## Full run

Needs: every key of [01_setup.md#environment-variables](01_setup.md#environment-variables) in `.env`, a clean [Dry run](#dry-run), and the operator's go-ahead: $562 at API prices in the 2026-11-20 run.

On macOS, one command:

```bash
./start-full-run.sh
```

It reads the token from `.env`, puts the real tier on the Claude API, runs the dry run and starts `job-configs/run-all.sh 3` under `caffeinate`, with its output also in `jobs/run-all.out`. On Linux, export what the script exports and start the runner yourself:

```bash
unset ANTHROPIC_API_KEY; export CLAUDE_FORCE_OAUTH=1 CLAUDE_CODE_OAUTH_TOKEN="$(grep '^CLAUDE_CODE_OAUTH_TOKEN=' .env | cut -d= -f2-)"
```

```bash
export CODECLIMB_BENCH_PI_AUTH="$(python3 job-configs/pi-auth.py anthropic)"
```

```bash
job-configs/run-all.sh 3
```

The run has three steps, all under `jobs/all-<stamp>-*/`:

1. **Reference grades, $0.** Both pins and the 6 maintenance bases. A grade without a reward, or a pin below reward 1, prints `reference grades failed: no trial started` and stops the run.
2. **Trials, 90.** 10 build jobs (2 stacks × `bare`, `skills`, `mcp-docs`, `full`, and `full × pocock`) and 20 maintenance jobs, 3 trials each, at most 3 jobs at a time. Each start prints `<time> start <job>, 3 attempts`.
3. **Regrades and code metrics, $0.** Then it prints `all done; analyze with: uv run python analyze.py ...`.

The protocol, what is pinned and how the 2026-11-20 run departed from one clean run: [docs/results/reproduce.md](../docs/results/reproduce.md).

Entry point: `job-configs/run-all.sh`.

## Continue a stopped run

Needs: a [Full run](#full-run) that stopped. On the first usage-limit stop `usage_watch.py` sends SIGTERM to every running job, keeps each trial's state and prints `stopped on a usage limit in: ...`; no new job starts.

Once the limit resets, pass the stopped run's prefix. Each job runs only the trials it still lacks, and the reference grades are reused:

```bash
CODECLIMB_CONTINUE="jobs/all-<stamp>" ./start-full-run.sh
```

Several stopped runs go in one value, space-separated. Delete a killed trial's folder first: a trial folder without a `result.json` counts as still running.

Entry points: `job-configs/run-all.sh` (`graded`), `usage_watch.py`.

## Regrade

Needs: finished trials under `jobs/`. $0: the verifier reruns on a trial's recorded artifacts, with no new trial.

The regrade rule: every build trial that is not `done` = 1, and every maintenance trial that is not resolved, is regraded once, and the regrade counts. `run-all.sh` does this itself; by hand:

```bash
python3 regrade.py jobs/all-<stamp>-regrades --slots 3 jobs/all-<stamp>-*-* jobs/all-<stamp>-references
```

After a verifier fix, regrade a whole job:

```bash
harbor job regrade jobs/<job dir> -p tasks/codeclimb-<stack>
```

Entry point: `regrade.py`.

## Code metrics

Needs: Docker running, build trials with a collected `/app`. $0. The analysis image builds on first use.

```bash
python3 code_metrics.py jobs jobs/all-<stamp>-*-*
```

Measures every build trial that has no `code-metrics.json` yet against its stack's pin, and writes the file into the trial folder. One build by hand:

```bash
python3 code_metrics.py --app <trial>/artifacts/app --stack inngest --out <trial>/code-metrics.json
```

Entry points: `code_metrics.py`, `analysis/measure.py`.

## Analysis

Needs: the job folders of a run, with its reference grades and regrades.

```bash
uv run python analyze.py jobs/all-<stamp>-*-* jobs/all-<stamp>-references jobs/all-<stamp>-regrades > jobs/report.txt
```

Writes `trials.jsonl`, one row per trial, into the first folder, and the report to `jobs/report.txt`: reward per cell, the hidden and real tests, the 2 × 2 arm effects per stack, the stack comparison, the maintenance trials, the metrics, and the trials kept out of every mean. [docs/results/metrics.md](../docs/results/metrics.md) is built from that report.

Read each trial the report lists as a leak by hand. If the operator clears it, add it with the reason to `LEAK_CLEARED` in `analyze.py` and to the benchmark spec's "cleared by hand" list, then rerun the analysis ([docs/results/reproduce.md](../docs/results/reproduce.md#leak-review)).

Other forms:

```bash
python3 analyze.py report jobs/<first dir>/trials.jsonl
```

```bash
python3 analyze.py counts jobs/<job>/<trial>/agent/trajectory.json
```

```bash
python3 analyze.py pile jobs/<job>/<trial>/artifacts/app
```

`counts` prints the skill, MCP and web calls of a trajectory; `pile` prints a `pocock` trial's build tickets, tickets done and commits.

Entry point: `analyze.py`.

Next: [03_how_it_works.md](03_how_it_works.md)
