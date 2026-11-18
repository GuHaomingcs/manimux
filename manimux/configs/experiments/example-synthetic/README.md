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

### Replay inference delays

Set the following in the shared `_base_.yaml` and run each demo variant. Each formal
request uses the next duration in milliseconds. Both rollouts finish after the fourth
request and the end of the active chunk, unless a rollout limit or operator stops them first.

```yaml
policy:
  options:
    delay_trace_ms: [80, 90, 320, 85]
```

To replay measured latency, replace the list with the path to a rollout's `events.jsonl`,
relative to the YAML that declares it. The loader reads `inference_response` events in
request order, skipping requests that expired before inference started. The resolved config
stores the input durations. The worker records its actual inference time separately, so
operating-system scheduling can add a small overhead. Warmup replays the same sequence independently and can repeat it.
Older recordings need an explicit list if they lack per-request measurements.

`manimux up` manages XPolicyLab and hosted-API deployments; this study has no model
service, so the two commands above are the whole deployment. The RoboGUI and runtime
ports are the defaults (8086, 5568, 5569); stop any other RoboGUI on this machine first.

The synthetic robot is not a kinematic model of any arm; the arms in RoboGUI move but the
poses carry no physical meaning. For a real station, continue with
[example-yam-pi05](../example-yam-pi05/README.md) or
[example-tianji-pi05](../example-tianji-pi05/README.md).
