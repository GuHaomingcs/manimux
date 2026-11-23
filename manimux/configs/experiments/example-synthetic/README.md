# Hardware-free study: synthetic robot and policy

[Back to ManiMux](../../../../README.md#quick-start) · [Deployment guide](https://sii-liulab.github.io/manimux/guideline.html#configuration)

Run the whole operator loop on any machine: RoboGUI, Prepare → Start → Finish, scoring,
counted trials, recordings and replay. The robot is a synthetic stand-in that echoes
commands back as state, and the policy is ManiMux's fake policy, so no station file,
camera, checkpoint, robot SDK or GPU is needed. Use it to learn the workflow before
touching a real station, or to test RoboGUI and recording changes.

```text
example-synthetic/
├── _base_.yaml        # synthetic robot + fake policy, Serial, RoboGUI, two layouts, scoring
└── demo/
    ├── serial.yaml    # base, nothing else
    └── async.yaml     # request the next chunk while the current one executes
../../lists/example-synthetic.yaml   # both methods, two counted trials each
../../local/synthetic.yaml           # empty station: no devices, services or model paths
```

Start RoboGUI and the runtime in two terminals:

```bash
uv run manimux-robogui --robot yam --host 127.0.0.1 --port 8086
uv run manimux run --config-list manimux/configs/lists/example-synthetic.yaml
```

Open **http://127.0.0.1:8086/**, choose an entry and **Prepare Experiment**, pick a layout,
then **Start rollout** and **Finish**. RoboGUI asks for the score; the trial counter
advances. Recordings go to `data/experiments/example-synthetic/synthetic_reach/<variant>/`
and appear in the recordings panel for replay.

To try one method without counting trials, pass `--config` instead:

```bash
uv run manimux run --config manimux/configs/experiments/example-synthetic/demo/serial.yaml
```

`manimux up` manages XPolicyLab and hosted-API deployments; this study has no model
service, so the two commands above are the whole deployment. The RoboGUI and runtime
ports are the defaults (8086, 5568, 5569); stop any other RoboGUI on this machine first.

The synthetic robot is not a kinematic model of any arm; the arms in RoboGUI move but the
poses carry no physical meaning. For a real station, continue with
[example-yam-pi05](../example-yam-pi05/README.md) or
[example-tianji-pi05](../example-tianji-pi05/README.md).

## Moving target benchmark

Run both demo schedules against a target on a 0.1 m radius circle, using a virtual clock:

```bash
python -m scripts.experiments.benchmark_tracking --delay-ms 80 90 320 85 --duration-s 12
```

Each run starts on target. At request time a scripted policy samples the current target
and plans a straight line from the measured position toward that sample at 0.4 m/s,
holding the sampled target once reached. The planar plant follows the executed command with a 0.1 s time constant.
Serial uses the demo's first-step-when-ready schedule. Async uses its progress trigger
and trims elapsed action steps. Both run the ManiMux preview scheduler, timeline and
direct executor without starting devices or a model server.

Delays repeat in request order. A response becomes available on the first control tick
at or after its delay, following submission. The fixed scoring window includes startup
and holds. Different request counts are expected. JSON gives time-weighted tracking
RMSE in millimeters, seconds outside the tolerance, and request counts, including any
response still pending at the end. The scores describe this simulated plant and policy.

Use one value such as `--delay-ms 100` for constant latency, `--speed-m-s 0` for a
stationary control, and `--tolerance-mm` to set the tracking tolerance (default 30).
