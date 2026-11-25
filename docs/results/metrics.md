# CodeClimb benchmark: final results

The full run of 2026-11-20 to 2026-11-24, with regrades on 2026-11-25. It covers 2 stacks (Inngest, LangChain), 5 build arms each and 10 maintenance tasks per stack. The harness is Claude Code 2.1.322 on Opus 5.5 (`claude-opus-5-5`) at medium effort, run by Harbor 0.25.0. Every cell has 3 trials.

The source is `jobs/report-final-20261125.txt` (`analyze.py` over every job folder of the run) and its `trials.jsonl`. [reproduce.md](reproduce.md) says how to rerun it. `docs/codeclimb-eval-spec.md` defines every term used here.

## Headline

- **Builds:** every one-shot and pocock cell reaches reward 1.0 on all 3 trials, except LangChain `mcp-docs`, where one trial scored 0.088.
- **No arm effect is detectable at n=3.** This holds for both reward and cost, whether skills, MCP docs or both are added.
- **Hidden and real tests are where builds differ.**
  - The one-shot cells pass 89–96% of them, except LangChain `full` at 82%.
  - The pocock cells pass 91% (Inngest) and 90% (LangChain), inside the one-shot range. Their real tier is 0.776 and 0.866.
  - 4 pocock trials (Inngest `EXCiiFN`; LangChain `LozkErs`, `cZcvXAp`, `uUkP7fH`) were first graded while the real tier's Copilot quota was failing, and scored 4–6/18 real tests. Regraded on the Claude API ($0, from their recorded artifacts), they score 10–15/17–18, and the regrade counts.
- **Maintenance:** Inngest resolves 27/30, LangChain 30/30.
- **Code quality:**
  - One-shot builds are about 0.6x the reference's size, with 2–20x its type escapes and lint findings, and about half its test coverage.
  - Pocock builds have about 5x the tests and reach the reference's coverage.
  - Every build's own tests pass in all 3 reruns.
- **Cost** (Claude Code's reported cost on the operator's subscription):
  - $511 for 31 build trials (including the leak trial) and $51 for 60 maintenance trials.
  - About $12–15 per one-shot build and $29–31 per pocock build.

## Build trials: reward

Reward is 1 when every basic check passes (the build works end to end); `done` is the count of trials at reward 1. $ is the mean per trial.

| stack | workflow | arm | n | rewards | mean | done | $ / trial | agent min |
|---|---|---|---|---|---|---|---|---|
| inngest | one-shot | bare | 3 | 1.0, 1.0, 1.0 | 1.000 | 3/3 | 12.65 | 46.9 |
| inngest | one-shot | skills | 3 | 1.0, 1.0, 1.0 | 1.000 | 3/3 | 11.57 | 45.8 |
| inngest | one-shot | mcp-docs | 3 | 1.0, 1.0, 1.0 | 1.000 | 3/3 | 13.49 | 71.1 |
| inngest | one-shot | full | 3 | 1.0, 1.0, 1.0 | 1.000 | 3/3 | 11.81 | 48.0 |
| inngest | pocock | full | 3 | 1.0, 1.0, 1.0 | 1.000 | 3/3 | 30.92 | 112.7 |
| langchain | one-shot | bare | 3 | 1.0, 1.0, 1.0 | 1.000 | 3/3 | 13.53 | 83.0 |
| langchain | one-shot | skills | 3 | 1.0, 1.0, 1.0 | 1.000 | 3/3 | 13.77 | 73.0 |
| langchain | one-shot | mcp-docs | 3 | 1.0, 1.0, 0.088 | 0.696 | 2/3 | 13.86 | 75.0 |
| langchain | one-shot | full | 3 | 1.0, 1.0, 1.0 | 1.000 | 3/3 | 15.01 | 78.1 |
| langchain | pocock | full | 3 | 1.0, 1.0, 1.0 | 1.000 | 3/3 | 29.23 | 110.3 |

The failed LangChain `mcp-docs` trial failed 31 of 34 basic checks; only install, image and typecheck passed.

**Pocock tickets done (mean):** Inngest 34.0, LangChain 31.3.

**Reference builds** (the build pins, Inngest `5a81c07` and LangChain `3612892`) score reward 1.0 under the same verifier. So do the 6 maintenance bases graded with them: Inngest `1360cb4`, `1452a93`, `bcabd72`; LangChain `400bd40`, `9911231`, `9d04590`.

## Build trials: hidden and real tests

These pass rates are reported beside the reward and are not part of it.
- **Hidden:** 40 robustness tests: crash, stop, pause, restart and deadline cases.
- **Real:** 17–18 tests on real nights (17 where `meter-costs` is skipped because no evaluation called a model), with the coder and reviewer on Claude Haiku through the Claude API: budget, deadline, metering, sandbox separation, overfit guards.
- **passed:** the share of hidden and real tests each trial passed.

| stack | workflow | arm | passed per trial | mean | hidden | real |
|---|---|---|---|---|---|---|
| inngest | one-shot | bare | 0.965, 0.93, 0.965 | 0.953 | 0.950 | 0.961 |
| inngest | one-shot | skills | 0.895, 0.93, 0.914 | 0.913 | 0.925 | 0.885 |
| inngest | one-shot | mcp-docs | 0.842, 0.912, 0.912 | 0.889 | 0.875 | 0.922 |
| inngest | one-shot | full | 0.947, 0.966, 0.947 | 0.953 | 0.933 | 1.000 |
| inngest | pocock | full | 0.947, 0.931, 0.845 | 0.908 | 0.967 | 0.776 |
| inngest | reference `5a81c07` | | 1.0 | 1.000 | 1.000 | 1.000 |
| langchain | one-shot | bare | 0.931, 0.914, 1.0 | 0.948 | 0.958 | 0.926 |
| langchain | one-shot | skills | 0.947, 0.982, 0.948 | 0.959 | 0.942 | 1.000 |
| langchain | one-shot | mcp-docs | 0.947, 0.86 | 0.904 | 0.900 | 0.912 |
| langchain | one-shot | full | 0.897, 0.655, 0.912 | 0.821 | 0.942 | 0.553 |
| langchain | pocock | full | 0.86, 0.947, 0.879 | 0.895 | 0.908 | 0.866 |
| langchain | reference `3612892` | | 0.966 | 0.966 | 0.950 | 1.000 |

- LangChain `mcp-docs` has n=2 here: the trial at reward 0.088 never reached the hidden and real tests.
- The LangChain reference fails `hidden.eval-keeps-failing` and `hidden.hard-deadline-mid-step`. The maintenance bases fail `hidden.config-rejects` and `hidden.hard-deadline-mid-step` across both stacks. So these tests are hard even for the reference builds.

**Tests failed most often:**
- **Hidden:** `continue-after-stop`, `pause-resume`, `hard-deadline-mid-step`, `backstop-mid-step` and `pause-timeout`, across nearly every cell.
- **Pocock, real tier:**
  - `deadline` failed in all 3 LangChain trials (each night stopped on `max_rounds`) and in 1 Inngest trial.
  - `feedback-reaches-coder` failed in 2 of 3 trials per stack: round 1's review feedback is missing from round 2's coder prompt.
  - Inngest `EXCiiFN`'s round 3 night hung for 30 min without a done.json or stop.json. That fails 6 real tests: meter-costs, spend-adds-up, keep-consistency, no-held-out-to-coder, reviewer-no-dev-item and eval-sandbox-separate.
  - `stop-halts-spend` failed in 1 trial per stack.
- **LangChain one-shot `full`, real tier:** one trial (`vqnw6xD`) errored on every real night.

## Arm effects (one-shot, within a stack)

These are exact permutation tests on the 2 x 2 design: skills (yes or no) by MCP docs (yes or no), with `full` as both. None is detectable at n=3.

| stack | metric | skills | mcp-docs | interaction | full − bare |
|---|---|---|---|---|---|
| inngest | reward | 0.000 | 0.000 | 0.000 | +0.000 |
| inngest | cost $ | −1.379 | +0.540 | −0.603 | −0.838 |
| langchain | reward | +0.152 | −0.152 | +0.304 | +0.000 |
| langchain | cost $ | +0.696 | +0.784 | +0.911 | +1.481 |

## Maintenance trials

These are one-shot runs of the `bare` arm on a broken (repair) or outdated (change) base.

- **resolved:** the trial's targets pass and nothing that passed on the base regressed. A trial's first grade can fail; the regrade counts, as for builds (one: Inngest r12 `XYGbXMF`, whose first grade failed `hard-stop`).
- **hidden passed:** the share of the 40 hidden tests the trial passed. Every base fails 2 of them, `config-rejects` and `hard-deadline-mid-step`, so 0.950 means the trial kept the base's level. The c6 and c7 targets are those two tests (`config-rejects`, `hard-deadline-mid-step`), so a resolved c6 or c7 trial reaches 0.975. A trial below its task's resolved level broke a hidden test: the unresolved c7 trial fixed its target and broke another (0.95).
- **No real tier:** maintenance trials grade only `basic` and `hidden` (`maintenance.FAMILIES`), so there are no real-test results.
- **$ / trial** and **agent min** are means per trial: Claude Code's reported cost and the harness's wall time.

| stack | task | kind | n | resolved | hidden passed per trial | mean | $ / trial | agent min |
|---|---|---|---|---|---|---|---|---|
| inngest | c2 | change | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 2.87 | 12.2 |
| inngest | c4 | change | 3 | 2/3 | 0.925, 0.95, 0.95 | 0.942 | 0.92 | 10.0 |
| inngest | c6 | change | 3 | 3/3 | 0.975, 0.975, 0.975 | 0.975 | 0.23 | 1.4 |
| inngest | c7 | change | 3 | 2/3 | 0.975, 0.95, 0.975 | 0.967 | 1.31 | 7.9 |
| inngest | r2 | repair | 3 | 2/3 | 0.95, 0.95, 0.925 | 0.942 | 0.47 | 5.0 |
| inngest | r3 | repair | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 0.46 | 3.8 |
| inngest | r10 | repair | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 0.72 | 9.0 |
| inngest | r12 | repair | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 0.30 | 3.7 |
| inngest | r14 | repair | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 0.47 | 9.7 |
| inngest | r15 | repair | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 0.43 | 11.1 |
| langchain | c2 | change | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 3.00 | 13.6 |
| langchain | c4 | change | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 1.24 | 15.3 |
| langchain | c6 | change | 3 | 3/3 | 0.975, 0.975, 0.975 | 0.975 | 0.20 | 1.4 |
| langchain | c7 | change | 3 | 3/3 | 0.975, 0.975, 0.975 | 0.975 | 1.08 | 9.8 |
| langchain | r2 | repair | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 0.52 | 6.9 |
| langchain | r3 | repair | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 0.37 | 6.1 |
| langchain | r10 | repair | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 1.01 | 9.1 |
| langchain | r12 | repair | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 0.36 | 5.0 |
| langchain | r14 | repair | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 0.57 | 16.5 |
| langchain | r15 | repair | 3 | 3/3 | 0.95, 0.95, 0.95 | 0.950 | 0.43 | 4.6 |
| inngest | all | all | 30 | 27/30 | | 0.953 | 0.82 | 7.4 |
| inngest | all | change | 12 | 10/12 | | 0.958 | 1.33 | 7.9 |
| inngest | all | repair | 18 | 17/18 | | 0.949 | 0.47 | 7.0 |
| langchain | all | all | 30 | 30/30 | | 0.955 | 0.88 | 8.8 |
| langchain | all | change | 12 | 12/12 | | 0.962 | 1.38 | 10.0 |
| langchain | all | repair | 18 | 18/18 | | 0.950 | 0.54 | 8.0 |

The 3 unresolved Inngest trials each broke a hidden test that passed on the base:
- c4 and c7 broke `hidden.continue-after-stop`;
- r2 broke `hidden.used-night-id`.

Cost per maintenance trial ranges from $0.16 (c6) to $3.41 (c2), with a mean of $0.85: $24.53 for the 30 Inngest trials and $26.36 for the 30 LangChain trials. The verifier took 43 min per Inngest trial and 34 min per LangChain trial on average.

## Code and practice metrics

`code_metrics.py` measures each counted build in a pinned analysis container. These metrics are reported only: none is a check or part of the reward.
- **What is measured:** TypeScript and JavaScript files, leaving out the given inputs, the Next.js app, generated files and anything the build's own git ignores.
- **lint/kloc:** findings of a fixed typescript-eslint ruleset per 1000 code lines.
- **type escapes:** `any`, non-null `!`, `as unknown as` and `@ts-` directives.
- **own tests green:** how many of 3 runs of the build's own `npm test` exit 0 in the analysis container. The tests get a Docker daemon of their own and the build's sandbox image, as in the trial, and no CodeClimb service. Line coverage comes from the same setup.

### Per cell (mean of 3)

| stack | workflow | arm | code lines | test lines | files | type escapes/kloc | lint/kloc | dup % | max complexity | line coverage % | own tests green /3 | unused files |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| inngest | one-shot | bare | 4822 | 235 | 31 | 30.9 | 172 | 0.3 | 82 | 30.4 | 3.0 | 0.0 |
| inngest | one-shot | skills | 4518 | 168 | 34 | 30.5 | 194 | 0.2 | 62 | 23.7 | 3.0 | 0.0 |
| inngest | one-shot | mcp-docs | 4695 | 164 | 34 | 27.0 | 161 | 0.3 | 76 | 24.6 | 3.0 | 0.3 |
| inngest | one-shot | full | 4466 | 195 | 33 | 33.3 | 172 | 0.2 | 82 | 27.1 | 3.0 | 0.0 |
| inngest | pocock | full | 6016 | 1468 | 67 | 20.2 | 73 | 0.3 | 54 | 71.7 | 3.0 | 3.0 |
| inngest | reference `5a81c07` | | 7947 | 1857 | 57 | 8.2 | 9.9 | 0.6 | 72 | 66.9 | 3 | 3 |
| langchain | one-shot | bare | 4808 | 157 | 31 | 33.5 | 194 | 0.2 | 75 | 30.3 | 3.0 | 6.3 |
| langchain | one-shot | skills | 4678 | 172 | 35 | 34.1 | 182 | 0.3 | 77 | 28.3 | 3.0 | 6.0 |
| langchain | one-shot | mcp-docs | 4514 | 203 | 31 | 42.2 | 207 | 0.5 | 89 | 37.1 | 3.0 | 3.3 |
| langchain | one-shot | full | 4886 | 315 | 31 | 36.8 | 185 | 0.4 | 69 | 32.9 | 3.0 | 0.7 |
| langchain | pocock | full | 5022 | 933 | 62 | 20.0 | 67 | 0.1 | 53 | 66.9 | 3.0 | 2.0 |
| langchain | reference `3612892` | | 8546 | 2012 | 85 | 0.9 | 13.0 | 0.35 | 67 | 67.0 | 3 | 7 |

### Per stack (all 15 builds)

| | inngest | langchain |
|---|---|---|
| code lines (vs reference) | 4904 (0.62x) | 4781 (0.56x) |
| files (vs reference) | 40 (0.70x) | 38 (0.45x) |
| glue lines / domain lines | 448 / 4010 | 612 / 3813 |
| type escapes per kloc (vs reference) | 28.4 (3.5x) | 33.3 (37x) |
| lint findings per kloc (vs reference) | 154 (15.6x) | 167 (12.8x) |
| duplicated % | 0.3 | 0.3 |
| complexity mean / max | 3.63 / 71 | 3.63 / 72 |
| line coverage %: all / glue / domain | 35.5 / 0.8 / 39.3 | 39.1 / 3.2 / 44.3 |
| unused files / unused exports | 0.7 / 55.9 | 3.7 / 52.9 |
| dependencies beyond the spec's table | 2.5 | 0.0 |
| own tests green, of 3 runs | 3.0 | 3.0 |
| hardcoded thresholds (builds with any) | 1/15 | 3/15 |

**Practices:**
- No build, and neither reference, has CI, pre-commit hooks, a linter or a formatter.
- A README is present in 8/15 Inngest builds and 11/15 LangChain builds; an AGENTS.md in 4/15 and 3/15.
- 1/15 Inngest builds and 10/15 LangChain builds keep the given tsconfig unchanged.

## Process and runtime metrics (per stack, mean of 15 builds)

| | inngest | langchain |
|---|---|---|
| agent time in tools / outside tools | 1810 s / 2049 s | 2868 s / 2139 s |
| feedback loop (mean tool wait) | 16.2 s | 29.2 s |
| services up at | 29.1 min, $6.65 | 30.3 min, $5.61 |
| night 1 done at | 32.0 min, $7.70 | 38.6 min, $8.12 |
| night 5 passes at (trials that got there) | 38.7 min, $8.87 (9/15) | 45.7 min, $9.11 (13/15) |
| TypeScript errors seen (in runs) | 14.7 (2.6) | 9.7 (2.7) |
| test failures seen (in runs) | 2.3 (1.9) | 1.5 (1.3) |
| cold start | 2.4 s (reference 11.1 s) | 198.0 s (reference 144.3 s) |
| resume latency | 46.3 s (reference 156.1 s) | 116.1 s (reference 122.4 s) |

**Web calls:**
- 1 Inngest build used WebFetch once.
- 4 LangChain builds ran 6 curl or wget calls in all, to non-local URLs.
- No build used WebSearch, and no maintenance trial made any web call.

## Trials kept out, and leaks cleared by hand

- **Leak, kept out:** `codeclimb-langchain__U3NPDfX` (LangChain one-shot `full`, $13.50). An extra trial, `o8xG5nj`, replaced it so the cell has n=3.
- **Leaks cleared by hand, counted.** Both were operator decisions, recorded in the spec and in `analyze.py` `LEAK_CLEARED`:
  - `codeclimb-langchain__gVLNHRW` (LangChain `skills`). Its one session hit is a `node -e` call of the build's own `blockedUrl(...)`, a string check that makes no request. Its `/app` hits were a `git clone` of the build into `/app/.vc`, whose files are byte-identical to the given files.
  - `codeclimb-langchain__o8xG5nj` (LangChain `full`). Its one hit is `curl -sI` (headers only) of astral-sh's python-build-standalone releases on github.com: a third party, not CodeClimb.
- **Infra errors:** 0.
- **Without a reward:** 0.
- **Replaced by their regrade:** 7 build trials and 9 maintenance trials. Under the regrade rule, a trial that did not pass is regraded once from its recorded artifacts, and the regrade counts.
