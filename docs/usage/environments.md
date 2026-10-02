# Local Python environments

`envs/` is a conventional location for local virtual environments, such as
`envs/yam/.venv`. It does not contain robot IPs, CAN bindings or experiment YAML.
Cloning the repository does not create these environments. Their contents are local
and ignored by Git; follow the selected deployment guide to create them.

| Location | Purpose |
| --- | --- |
| Root `.venv/` | ManiMux core, development tools and offline RoboGUI; managed by the root project |
| `envs/yam/.venv/` | YAM runtime, i2rt, cameras, RoboGUI and optional offline replay dependencies |
| `envs/tianji/.venv/` | Tianji/TacCap hardware dependencies, prepared with the body runbook |
| `envs/aloha/.venv/` | ALOHA/PiPER RoboGUI and optional ARX/PiPER SDKs; hardware validation pending |
| Model-specific environment | XPolicyLab model inference/training, such as `XPolicyLab/policy/Pi_05/openpi/.venv/` |
| Existing `envs/umi_dp/`, `envs/xr1/`, etc. | Local environment conventions still referenced by some model launchers; follow their runbooks |

The hardware process does not need torch/JAX to consume Pi05 predictions from a separate
model service. An interpreter path alone does not identify the imported ManiMux checkout:
that depends on its installation and import path. Install the intended checkout into the
appropriate environment instead of treating an old interpreter path as a source migration.

## Installation entry points

- First connection to your own robot: [local station setup](station.md).
- YAM SDK: [YAM component README](../../manimux/embodiments/arm/yam/README.md).
- Offline assets: [ALOHA](aloha.md) · [PiPER](piper.md).
- ARX/PiPER: [SDK installation](robot-sdks.md) · [controller adapters](can-arms.md).
- Cameras: [RealSense README](../../manimux/embodiments/sensor/realsense/README.md).
- Tianji/TacCap: [deployment runbook](../deployment/umi-dp-tianji-taccap.md).
- Models: [deployment runbook index](deployments.md#model-and-robot-recipes).

Hardware/model environments are usually created with `uv venv`, then populated with
`uv pip install --python`. When adding dependencies, target the interpreter explicitly:

```bash
uv pip install --python envs/yam/.venv/bin/python -e '.[replay,realsense,xpolicylab]'
```

Do not point root-project `uv sync` or `UV_PROJECT_ENVIRONMENT` at an existing independent
hardware/model environment: syncing the root lockfile can remove SDK/model dependencies
not declared there. Manage the root development environment through the root project normally.

## YAM EEF regression environment

EEF regression checks use actual offline YAM geometry and the i2rt IK solver.
They need SDK dependencies but never construct a motor session. Create a separate
environment so installing this pinned SDK does not replace the PiPER/ARX environment:

```bash
uv venv --python 3.12 envs/yam/.venv
printf 'scikit-build-core<0.10\n' > envs/yam/i2rt-build-constraints.txt
uv pip install --python envs/yam/.venv/bin/python \
  --build-constraint envs/yam/i2rt-build-constraints.txt \
  -e '.[starvla,replay]' pytest opencv-python-headless \
  'i2rt @ git+https://github.com/i2rt-robotics/i2rt.git@5d47b358bafb30c65e397f2ece506550a0db4594'
uv pip check --python envs/yam/.venv/bin/python
```

The build constraint follows the pinned i2rt source's requirement for ruckig's
source build. A compiler and CMake are needed on a fresh installation. The core
package supplies MuJoCo; i2rt supplies Mink and its QP solver dependencies.
This environment contains no learned-model runtime such as torch/JAX.

With the ignored local regression suite available, run:

```bash
envs/yam/.venv/bin/python -m pytest \
  tests/unit/test_pose_adapter.py \
  tests/integration/test_starvla_eef_runtime.py
```

These checks exercise the real native protocol, offline IK, decoder processes,
runtime/executors and recorder with synthetic predictions. They do not load
learned checkpoint weights or certify physical robot behavior. Keep output
reports under the ignored local workspace.

## Different from configuration

- `manimux/configs/`: experiments, assemblies, inference, executors, model-service settings
  and station templates. The private `manimux/configs/local/station.yaml` binds local devices.
- [Policy recipes](../../manimux/configs/policy/README.md#model-layout-passed-to-xpolicylab): model-side action dimensions
  and batch size, passed to XPolicyLab through experiment configuration.

Environment locations and all model launchers have not been unified into one layout.
They should not be confused with the robot's CAN, serial and IP bindings.

## Offline regression tests

Tests, fixtures and test launchers are local development resources and are excluded
from Git. Keep useful regression checks locally; do not force-add them to commits.
A fresh clone does not include `tests/`, so the commands below require a local test
suite. Formatting and lint commands are listed in [Contributing](../development/README.md#contributing)
and work without that directory.

Run runtime and component tests with the runtime interpreter, from the repository root:

```bash
envs/yam/.venv/bin/python -m pytest tests/unit
envs/yam/.venv/bin/python -m pytest tests/integration/test_xpolicylab_worker.py
```

These tests use synthetic observations, fake devices and local test servers. They do
not establish real-robot readiness. Tests that require the private Tianji SDK or
TacCap geometry explicitly skip when those resources are absent; generic interface
tests still run. Use `-rs` to see the missing prerequisites.

Model-side checks need the matching model environment. For example:

```bash
XPolicyLab/policy/Pi_05/openpi/.venv/bin/python -m pytest tests/unit/test_pi05_yam_eef.py
```

That module skips in a runtime environment without OpenPI. Installing model packages
into the hardware environment is not required. Inspect old local tests for obsolete
interfaces before including them in a regression run.
