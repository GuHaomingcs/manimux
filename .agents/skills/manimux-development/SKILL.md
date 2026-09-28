---
name: manimux-development
description: Develop or review ManiMux components, embodiments, policy integrations, runtimes, executors and experiment interfaces. Use to inspect the current architecture, determine which layer a request actually changes, route to the relevant protocol, and present a reviewable staged plan before editing. Use station setup instead for binding an already supported system to local devices and addresses.
---

# ManiMux Development

Read the repository `AGENTS.md` and relevant nested instructions first. Paths below
are relative to the repository root; `references/` links are relative to this skill.
This skill governs development and integration. It does not authorize hardware
startup or replace the user's review of a proposed change.

## What following the protocol means

A component follows its protocol when its caller can use the existing interface
without knowing the vendor or model name. Matching method names is insufficient:
inputs, outputs, units, action meaning, timestamps, resource ownership and failure
behavior must also agree. Different kinds of components have different interfaces;
a camera, a gripper and a policy client need not share one universal base class.

Integrate at the owning layer. Do not make an integration work by spreading device
names, wire-format parsing, geometry or experiment parameters through the main loop.
Do not fix this by adding another registry, configuration framework, generic wrapper
or repeated validation in every layer. Use existing loaders and check a constraint
where the corresponding data enters or changes meaning.

## Inspect before classifying

Do not classify an upstream project from its name, README label or directory shape.
The same request may mean adding one model to an existing framework, integrating a
complete peer framework, supporting a new embodiment, or combining several changes.

Before proposing files or editing:

1. Inspect the current branch and working tree. Preserve unrelated work.
2. Read the selected experiment or nearest relevant configuration and follow its
   actual loader, factory, public interface, one current implementation, callers and
   focused tests.
3. Inspect the upstream runtime boundary when one is involved: determine who loads
   models, owns dependencies and sessions, exposes inference and supports multiple
   models or tasks.
4. Trace the task's real data and control path through current code. Old runbooks,
   compatibility paths and synthetic tests are evidence, not automatic templates.
5. Separate facts found in code from assumptions and decisions needed from the user.

Use this compact map for orientation, then show the user only the levels relevant to
the request:

```text
Model / Policy Framework
          <->
      Policy Client
          <->
      Policy Adapter
          <->
     ManiMux Runtime
          <->
    Executor / Safety
          <->
      Robot Assembly
          <->
 Arm / End Effector / Sensor
          <->
       Physical Hardware
```

Configuration composes these layers. A private station binds an already supported
composition to one machine. Viewer and recording observe runtime evidence without
owning inference or robot control.

## Resolve the development dimension with the user

After inspection, state the most likely classification and the evidence for it. When
two interpretations lead to different ownership or directories, present those concrete
alternatives and ask the user to choose. In particular, never guess whether an upstream
project is one learned model or a reusable framework: explain how the implementation
would differ under each interpretation before requesting confirmation.

If the request is already unambiguous, state the classification and proceed to the
plan; do not ask the user to repeat established facts. If it spans multiple dimensions,
identify the primary boundary, dependent boundaries and implementation order instead
of forcing the whole request into one category.

Current dimensions include physical components, robot assembly and geometry, learned
models, peer policy frameworks, policy clients, observation/action adapters, inference
scheduling, timelines, executors, safety, Viewer/recording and configuration. This is
orientation, not a closed taxonomy.

## Present a concrete plan before editing

Give the user a task-specific plan containing:

- the requested outcome, proposed classification and supporting evidence;
- a small architecture or call-flow diagram for the affected path;
- existing interfaces and configuration selectors that will be reused;
- files or directories expected to change, with each one's responsibility;
- input/output semantics, timing, reset behavior and resource ownership as relevant;
- an explicit scope lock: what will change and which established layers, deployments
  and semantics will remain unchanged;
- staged implementation order for a composite request;
- focused validation per stage and evidence that will remain unavailable.

Wait for the user's confirmation of this concrete plan before editing. If later
inspection changes the classification, file scope or protocol, update the plan and
confirm the changed scope before continuing.

## Route to the confirmed protocol

Read only the reference needed for the confirmed stage:

- [Components](references/components.md): arms, shared controllers, end effectors,
  offline geometry, robot assemblies, cameras and runtime sensors.
- [Policies](references/policies.md): learned models, peer frameworks, backend clients,
  action formats, policy adapters and independent decoding.
- [Runtime and configuration](references/runtime-config.md): inference strategies,
  timelines, executors, safety, Viewer/replay/recording and YAML ownership.

For device, endpoint and local path binding of an existing integration, use
`.agents/skills/manimux-station-setup/SKILL.md` instead. A development request may
include a station-template change, but real device values remain private station data.

The references describe protocols that exist today. Verify them against current code
before relying on exact signatures or behavior, and update a reference when its public
contract changes.

## Handle a genuinely new dimension openly

When the requested capability does not fit an existing layer, say so explicitly.
Do not force it into the nearest directory or invent compatibility with an unrelated
interface. Trace how it exchanges data with the current system, propose a small number
of ownership and boundary options with tradeoffs, and let the user select the design.

After that choice, define the new protocol before implementation. At minimum establish
inputs and outputs, semantics and timing, lifecycle and resource ownership, configuration
selection, failure behavior, compatibility boundary and validation. These requirements
make the design reviewable without prescribing what the new capability must be.

## Review the integration, not just whether it runs

For each affected boundary, establish:

- **Discovery:** Which config field and factory select it? Can another component
  of the same capability replace it without editing `runtime/edge.py`?
- **Data:** What are the group names/order, shapes, units, coordinate frames,
  quaternion convention, gripper meaning and absolute/delta anchor?
- **Ownership:** Who opens and closes the device/session? Can offline model loading,
  adapter construction and Viewer replay avoid hardware connections?
- **Behavior:** Are reset, cached/stale data, unsupported capabilities and failures
  handled explicitly at the owning boundary? Were existing semantics preserved?
- **Evidence:** Does the test traverse the real loader or public interface? State
  what was verified offline and what still requires an SDK, checkpoint or hardware.

Choose checks relevant to the change; do not create a blanket validator or a test
that merely repeats implementation details. Useful existing examples under
`tests/unit/` include `test_component_protocols.py`, `test_yam_assembly.py`,
`test_composed_kinematics.py`, `test_orbbec_sensor.py` and `test_action_replay.py`.
Runtime tests commonly use `envs/yam/.venv/bin/python`; model-side tests need their
own model environment. Missing SDKs are evidence limits, not reasons to fabricate
a successful integration.

## Compatibility is not a template

Describe compatibility paths when they affect the task, but do not copy them before
tracing why they exist. Preserve specialized semantics, constraints and failure behavior
unless their migration is part of the confirmed plan. Do not expand a new integration
into unrelated cleanup. A directory or passing mock test alone does not prove a backend,
robot or sampling mode is supported.

## Implement composite work in reviewable stages

Derive stages from actual dependencies rather than imposing one fixed sequence. A common
shape is to establish the boundary and contract, implement the lowest independent layer,
connect one real caller and callee, add configuration, validate offline, then add user
documentation and environment-specific verification.

For each stage:

1. Restate the agreed files, protocol and scope lock.
2. Implement only that stage while preserving unrelated changes.
3. Exercise the real loader or public interface with the smallest meaningful check.
4. Report what changed, what passed and what remains unverified.
5. Pause for review before the next stage unless the user explicitly requested all
   remaining agreed stages to proceed continuously.

## Development versus use

For device binding use `.agents/skills/manimux-station-setup/SKILL.md`.
Teleoperation/demonstration collection is outside this repository; retain runtime
recording and offline replay.

Deliver a short explanation of the extension point, configuration, focused checks and
remaining limitations. Update the relevant protocol reference when its public interface
changes, and update user documentation only after the supported path is concrete. Write
new comments and general documentation in English. Commit or push only when requested;
development work alone does not authorize starting services or moving hardware.
