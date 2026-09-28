# StarVLA validation and Pi feature coverage

The independent StarVLA serving path was checked on 2026-09-28. Results here use
`starvla_ws` and the native `StarVLA/` service. Earlier XPolicyLab-adapter results
are not evidence for this path. No physical robot, camera or CAN interface was used.
A completed offline rollout is not a manipulation success rate.

## Functional coverage

| Existing ManiMux Pi functionality | StarVLA path and evidence |
| --- | --- |
| Separate model and robot environments | Native StarVLA service and transport-only `starvla_ws` client |
| Ordered RGB, instruction, joint state | Explicit contract; real OFT and PI-v3 checkpoints |
| EEF state, pose output and FK/IK | Generic `PoseAdapter`; synthetic dual-arm YAM contract and real LIBERO model output |
| Absolute and observation-relative poses | Base/tool anchors, quaternion/axis-angle conversion and whole-chunk IK rejection |
| Reset and backend identity | Per-connection reset, episode-local DVAC state, checkpoint/shape/semantics checks |
| Serial, ManiMux async, temporal ensemble | Existing runtime strategies; no backend-specific scheduling loop |
| RTC, PAINT, AAC, AutoHorizon, DVAC | Real flow-head hooks and native request metadata; joint deployment only |
| Direct, smooth and MPC executors | Existing executors and recorded offline runtime checks |
| Independent decoding and parallel arm IK | Existing decoder process interface; real YAM geometry |
| Recording, Viewer and replay | Existing canonical joint records, RGB videos and offline Viewer path |

This aligns the deployment interfaces, not the training architecture or weights.
Pi's joint+EE training variant is not a StarVLA checkpoint. A joint-only checkpoint
cannot be relabeled as an EEF policy. The Pi05 YAM EEF adapter itself rejects RTC
conditions; this integration likewise does not advertise conditioned EEF sampling.

## Real checkpoints

Every transport probe sends initial input, repeated input, input after reset and
changed RGB. It verifies identity, dimensions, finite output and action conversion.
OFT and deterministic FAST reproduce repeated/reset predictions. Flow models sample
fresh noise; reset clears episode state without reseeding the model.

| Checkpoint | Native output | Offline environment |
| --- | --- | --- |
| Qwen3-VL-2B OFT, RoboTwin step 40000 | 50 × 14 absolute joints | Synthetic dual-arm joint plant |
| Qwen3-VL-4B PI-v3, RoboDojo step 100000 | 50 × 14 absolute joints | Synthetic joint plant; AAC uses offline YAM geometry and fixture calibration |
| Qwen2.5-VL GR00T, LIBERO step 30000 | 8 × 7 feedback EEF deltas | Analytic Cartesian plant, not Franka dynamics |
| Qwen2.5-VL FAST, LIBERO step 30000 | 8 × 7 feedback EEF deltas | Same analytic EEF path, strict action-token validation |

The five PI-v3 specialized sampling requests passed with real weights. The tested
GR00T EEF recipe exposes default inference only; small real GR00T heads exercise
the specialized hooks independently. PI-v3 GPU validation used bfloat16 and a
private two-GPU VLM placement helper because of available memory. That helper did
not replace model computation, normalization or sampling and is not a deployment
feature of this contribution.

Seventeen real-weight runtime runs each completed 500 control steps with zero
rejected plans (8,500 control steps in total):

| Checkpoint / runtime | Executor | Accepted plans |
| --- | --- | ---: |
| OFT / serial | direct | 11 |
| GR00T / serial | direct / smooth / MPC | 21 / 21 / 21 |
| FAST / serial | direct / smooth / MPC | 10 / 9 / 9 |
| PI-v3 / serial | direct | 8 |
| PI-v3 / ManiMux async | direct / smooth / MPC | 20 / 19 / 19 |
| PI-v3 / temporal ensemble | direct | 20 |
| PI-v3 / RTC | direct | 8 |
| PI-v3 / PAINT | direct | 6 |
| PI-v3 / AAC | direct | 2 |
| PI-v3 / AutoHorizon | direct | 3 |
| PI-v3 / DVAC | direct | 4 |

Recorded timestamps, finite command arrays and RGB videos were reopened after the
runs. These counts establish completion and data integrity on the configured
synthetic plants; they do not measure policy quality or physical task success.

## Synthetic multi-step EEF verification

The local EEF integration suite uses the actual native WebSocket server, client,
worker, adapter, YAM geometry, decoders, schedulers, executors and recorder. Model
computation supplies explicitly labeled synthetic poses. Its 16D EEF observations,
50 predicted poses and 20-step IK prefix exercise the same timing/control boundary
as the Pi05 YAM EEF adapter.

Nine tests passed: eight 300-step runtimes with zero rejected plans, plus comparison
against the Pi05 decoder and whole-chunk rejection on one-arm IK failure. Runtime
cases cover inline/single-process/parallel-arm decoding, smooth/MPC, async/serial/
temporal ensemble and absolute/observation-base/observation-tool targets.
**No matching real dual-arm multi-step EEF checkpoint was validated.**

## Focused checks and reproduction

| Check group | Passed | Scope |
| --- | ---: | --- |
| ManiMux client, codecs, recipes, pose adapter and shared AAC | 57 | Native wire, permutations, identity, reset, failures, configuration and action conversion |
| Runtime identity and architecture | 4 | Matching/mismatched backends, sampler capability guard and public policy dependencies |
| EEF runtime integration | 9 | Synthetic model output and actual YAM FK/IK/runtime/recording |
| Existing Viewer/action replay | 10 | Playback, scene construction and existing control/message path |
| StarVLA numerical/model and protocol checks | 35 | Small flow heads, training transforms, FAST validation, attention selection and legacy native RPC compatibility |

ManiMux's current repository policy keeps regression tests local. This
contribution's additional native model/protocol checks live outside the StarVLA
checkout, under the ignored `tests/starvla_native/` directory. They are validation
artifacts and are excluded from both contributions. Existing upstream StarVLA tests
remain untouched. Reusable offline fixtures and the public probe are included under
`scripts/validation/`; follow the [runbook](starvla-offline-runbook.md) for the
checkpoint-backed checks available to other contributors.

The deployment validation passed 105 focused checks: 57 ManiMux integration unit
checks, 35 native model/protocol checks, four runtime identity/architecture checks
and nine synthetic EEF runtime checks. The ten Viewer checks and real-weight runs
were completed separately. CPU model checks may emit CUDA/autocast warnings; they
are distinct from GPU checkpoint inference. This is not a full test run for both
repositories.

The PI-v3 capability regressions exercise successful canonical AutoHorizon inference
and reject legacy forwarding at startup: legacy forwarding uses cross-attention,
which cannot supply the required action-attention map. Its other supported flow
modes remain available.

## Parity scope

Coverage refers to the existing **ManiMux Pi deployment interfaces**: the listed
joint/EEF contracts, eight runtime modes, three executors, independent/parallel IK
decoding, reset, identity/capabilities and recording/replay. It does not certify
every combination of these features for every StarVLA checkpoint.

Pi05 also exposes batch observation/action methods in XPolicyLab. ManiMux's
`PolicyModel` deployment loop uses one robot observation per request; configured
StarVLA serving follows that contract. XPolicyLab's standalone batch evaluation API
and training workflows are outside this parity claim.

## Limits

- Only the listed checkpoint contracts were exercised. This does not certify every
  StarVLA backbone/head combination or checkpoint/embodiment pairing.
- OFT/FAST do not provide the specialized flow modes. AutoHorizon and DVAC enforce
  their actual attention/denoising-step requirements at startup and per request.
- FAST can produce invalid coefficients for some inputs; those responses raise
  errors instead of becoming zero actions. Arbitrary-input robustness is unproven.
- PAINT delay must cover serving latency. Stale plans and incompatible identities
  remain errors; none of these checks is disabled to obtain a passing rollout.
- Synthetic AAC calibration is not a physical ARX metric. Use the deployment's actual
  robot geometry and dataset statistics before making behavior comparisons.
- Training reproduction, a fresh environment install, simulator task evaluation and
  physical robot deployment have not been validated here.

## Assets and provenance

StarVLA source is based on upstream revision
`312fac890ab75b7651d2bc4f8f8c8dbb5e055184`. The parent gitlink pins the published
serving revision in the StarVLA fork. Native source and third-party licenses stay
in StarVLA.
The XPolicyLab submodule is unchanged by this integration.

The public assets used below retain their original configuration and statistics.
OFT and GR00T weights were supplied locally and are not distributed here.

| Asset | Source | Revision |
| --- | --- | --- |
| PI-v3 RoboDojo | [StarVLA PI-v3](https://huggingface.co/StarVLA/StarVLA-Qwen3vl4b-PIv3-RoboDojo) | `c119685777cf17d27940b9f36fbc7a83663361e0` |
| FAST LIBERO | [StarVLA FAST](https://huggingface.co/StarVLA/Qwen2.5-VL-FAST-LIBERO-4in1) | `2a30a316ab65ab1a3172082fa7ef4b7121beb447` |
| FAST VLM | [Qwen2.5-VL-3B-Instruct-Action](https://huggingface.co/StarVLA/Qwen2.5-VL-3B-Instruct-Action) | `97163e6190ca87d6abae7a4dd15840cadde2da1d` |
| FAST processor | [physical-intelligence/fast](https://huggingface.co/physical-intelligence/fast) | `ec4d7aa71691cac0b8bed6942be45684db2110f4` |

Use `hf download <repository> --revision <revision> --local-dir <destination>`
for the listed assets, preserving the run/checkpoint layout expected by StarVLA.
Keep weights under `checkpoints/pretrained/starvla/`; the `hf` CLI belongs to the
model environment. Reports, arrays, videos and local asset paths are excluded from
contribution commits. Attach summarized evidence to a PR rather than model weights.
