# Experiment Infrastructure

Current per-task result tables and setting decisions are maintained in the
[experiment register](../experiments.md); this document describes the operational and evidence contract.

Operator-facing screenshots, button meanings and the complete state flow are in the
[Viewer visual tutorial](viewer-tutorial.html). This document keeps the experiment data contract and
fair-comparison rules.

This document defines the operational contract for repeated real-robot evaluation. Model loading,
camera services and hardware preflight remain in each model runbook; the experiment layer does not
start or modify them.

## 1. Two runtime entry points

```bash
# One rollout, controlled from the terminal
manimux run --config <experiment.yaml>

# Persistent runtime service, controlled from Viewer
manimux serve --config <experiment.yaml>
```

`run` preserves the original CLI workflow. `serve` keeps the selected config available while Viewer
creates isolated rollouts. It does not launch a Policy Server, camera server or Viewer.

## 2. Viewer modes

Viewer exposes a prominent `Experiment mode` switch before each rollout:

| Mode | Intended use | Human reward |
|---|---|---|
| **OFF** | Deployment, debugging and demonstrations | No scoring step |
| **ON** | Formal pilot or benchmark collection | Save or skip evaluation after a finalized rollout |

The mode is locked at Prepare. For an experiment rollout, select a reference gallery and
slot `01`–`10` in the Top overlay, plus `Experiment repeat` `1`–`3`. Prepare freezes the
image identity and repeat; there is no separate editable layout ID.

The task text shown in Viewer is not decorative: the value present when `Prepare new rollout` is
clicked is copied into that rollout config and sent to the policy.

## 3. Operator flow

After the model server, camera server, Viewer and `manimux serve` are independently ready:

1. Confirm the task command; for an experiment rollout, choose the reference image and repeat.
2. Click `Prepare normal rollout` or `Prepare experiment rollout`.
3. Wait for `PAUSED`, inspect the physical setup, then click `Start rollout`.
4. Use `Pause / Hold` only when execution must stop without ending the rollout.
5. Click `Finish & Home` after success, failure or timeout.
6. Wait for Recorder finalization and the robot's configured shutdown/home sequence.
7. If experiment mode is ON, select `success`, `failure` or `invalid`, add any failure tags
   and notes, then click `Save evaluation`, or click `Skip evaluation` without filling
   the fields. Skipping does not create `evaluation/human-label.json` or assign a task result.
8. Prepare the next rollout only after the service reports ready.

`Pause / Hold` holds the current commanded position; it does not return home. The advanced recovery
control can request the configured home path without ending the rollout. `Finish & Home` finalizes
the episode and then follows the runtime's configured shutdown sequence.

## 4. Evidence contract

```text
data/experiments/<campaign>/<algorithm>/session-*/
├── session-manifest.json
└── rollout-001/
    ├── meta.json
    ├── events.jsonl
    ├── result.json
    ├── data.zarr/
    │   ├── ticks/
    │   └── plans/000000/
    │       ├── canonical_raw/
    │       ├── infra_output/
    │       └── committed/
    ├── videos/
    │   ├── <camera>.mp4
    │   └── index.json
    └── evaluation/
        └── human-label.json
```

- `session-manifest.json` stores the resolved configuration in `config`, the entry YAML's byte
  hash in `config_sha256`, and ManiMux/XPolicyLab git SHAs. The hash is not a digest of the resolved
  configuration, all dependencies, or dirty source.
- `meta.json` records task, layout, algorithm, experiment mode and the Policy Server fingerprint.
  New experiment rollouts also record `repeat_id` and `reference_layout` (`task`, absolute `path`,
  `sha256`). The gallery task is distinct from the policy prompt and canonical evaluation task.
  These per-attempt fields are frozen at Prepare and also published for Viewer reconnection.
  Ordinary rollouts have no formal layout/repeat identity. Image hashes do not preserve overwritten
  files; keep formal references unchanged. Legacy episodes without these fields remain unknown.
- `canonical_raw` is the decoded policy chunk before the inference strategy.
- `infra_output` is the chunk after the selected inference strategy.
- `committed` is the final horizon accepted by Timeline after trimming or blending.
- `ticks` stores measured state, scheduled reference, and command. The command is the executor
  output recorded after `robot.send_command()` returns; it is not a hardware acknowledgment.
  New recordings omit `optimized`, which previously duplicated `command` exactly. Existing
  recordings remain unchanged and may contain that historical field.
- `videos/index.json` stores camera timestamps, frame counts, dropped bundles and encoder errors.
- `human-label.json` exists only when an operator saves an evaluation. New labels use
  `human-label-v2` without a smoothness score. Historical v1 files remain unchanged;
  their task results remain usable and their old smoothness field is ignored.
- `result.json.success` means the runtime finalized normally; it is never task success.

Video recording is best-effort and asynchronous. A full video queue drops video bundles rather than
blocking the robot control loop. Formal analysis must inspect `dropped_bundles` and `error`. Track
task, seam, and PRM eligibility separately: unusable video does not erase a saved human task outcome.

### Recording coverage audit — 2026-09-28

Viser displays runtime messages and saves human assessments/layout references; `EpisodeRecorder`
persists the rollout trajectories and videos. GUI visibility does not prove persistence.

| Evidence | Current coverage | Evaluation consequence |
|---|---|---|
| Human assessment | Task result, reviewer/mode, tags and note; skip leaves no file; save replaces one sidecar | Missing is unreviewed; no multi-reviewer history |
| State/reference/command | RUNNING ticks and control timestamps; original state sample timestamp/sequence absent | Do not claim complete motion through pause/home or exact sensor-age reconstruction |
| Plan lineage | Decoded canonical, strategy output and committed arrays; acceptance/boundary diagnostics | Keep all three stages; accepted is not necessarily executed; no dedicated takeover event or complete timestamped pause/resume segmentation |
| Video | Per-camera MP4, encoded-frame capture times, dropped bundles and errors | Keep indexes and tick camera times; PRM still needs view/time alignment checks |
| Request reproduction | Request IDs and some strategy-specific diagnostics | Full chosen observations, raw model output and rejected plan arrays are not saved; decoded canonical is not model-raw |
| Experiment provenance | Resolved config, per-rollout task/layout/repeat/reference hash/backend metadata and repository HEADs | Setting version, canonical task mapping, block/seed, dirty code and complete weight identities still need an explicit analysis mapping |

`ticks.inference_ms` repeats the most recent accepted inference value; do not average control ticks
to obtain per-request latency. The current handoff plotter pairs adjacent accepted plans and clamps
an expired outgoing plan to its endpoint. It is an exploratory tool, not a complete cross-algorithm
seam evaluator. Review boundary classes and missing timing evidence before filling formal results.

The experiment skill documents the concrete read/evaluate/report workflow:
[ManiMux experiments](../../.agents/skills/manimux-experiments/SKILL.md). These recording gaps are
identified work, not capabilities added by the skill.

## 5. Fair pilot checklist

Before comparing algorithms:

- use the same checkpoint, norm stats, task text, home/start state and physical layout definition;
- warm the model server before timed rollouts;
- assign an explicit layout ID and randomize algorithm order;
- freeze each algorithm config and preserve its config hash;
- count attempts, valid rollouts, invalid rollouts and safety stops separately;
- inspect the backend fingerprint so a restarted service did not load another checkpoint;
- tune on development layouts, then stop changing parameters on test layouts;
- derive automatic metrics only after matching trajectories, videos and human labels.

### Historical operator-randomized layout replay

The earlier pilot below used free-form layout IDs. The current campaign uses the ten saved
reference slots and three repeats per model/method in the [experiment register](../experiments.md).

For the YAM pilot, the operator may freely place task objects inside the task's declared workspace.
That freedom is sampled once per matched block, not once per algorithm:

1. Assign a readable `layout_id` and place the objects.
2. Use the initial top-camera frame as the layout reference.
3. Run every compared algorithm once in a randomized order.
4. Restore the same layout from the reference frame before each rollout.
5. Complete the configured repeats before sampling a new layout.

If the scene cannot be restored closely enough, mark that attempt `invalid`; do not silently replace
it with an easier layout for only one algorithm. A future Viewer overlay may assist restoration, but
the fairness rule does not depend on that UI feature.

See [experiment design](experiment-design.md) for the study matrix and reporting rules.
