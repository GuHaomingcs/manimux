# Choose a policy deployment

Choose the framework, checkpoint, action representation and embodiment together.
A checkpoint is not portable to another robot just because its output width matches.
Use the matching experiment on the runtime and model server, and bind local paths
in your station file where that launcher supports it.

## Model and robot recipes

| Deployment | Guide |
| --- | --- |
| Pi05 / OpenPI on YAM | [Joint](../deployment/pi05-yam.md) · [EEF](../deployment/pi05-yam-eef.md) |
| DP on YAM | [Absolute EEF](../deployment/dp-yam.md) |
| SAPolicy on YAM | [Joint/EEF and camera mapping](../deployment/sapolicy-yam.md) |
| GR00T N1.7 on YAM | [Deployment and RTC](../deployment/gr00t-yam.md) |
| LingBot-VLA2 on YAM | [Action semantics and deployment](../deployment/lingbot-vla2-yam.md) |
| Xiaomi XR-1 | [YAM](../deployment/xiaomi-xr1-yam.md) · [Tianji–TacCap](../deployment/xiaomi-xr1-tianji-taccap.md) |
| UMI DP on Tianji–TacCap | [Artifact binding and services](../deployment/umi-dp-tianji-taccap.md) |
| OpenWAM on YAM | [Checkpoint contract](../deployment/openwam-yam.md) |
| StarVLA | [Offline deployment](../deployment/starvla-offline.md) |
| Cosmos3 / Isaac 0.5 | [Cosmos3](../deployment/cosmos3-offline.md) · [Isaac 0.5](../deployment/isaac05-offline.md) |

Model dependencies run in their own environments. The hardware runtime does not
need torch or JAX merely to talk to a policy server. Follow the selected framework's
installation instructions and [environment guidance](../../envs/README.md).

## What support means

XPolicyLab and StarVLA are peer policy frameworks. Model implementations stay with
the owning framework; ManiMux clients handle transport and capability/identity
checks. [XPolicyLab bridge](../deployment/xpolicylab.md).

YAM and Tianji–TacCap have assembly integrations with different SDK and asset
requirements. Direct, Smooth and MPC are executors, independent of inference
strategies. The [integration protocols](../development/README.md) describe these boundaries.

A recipe, successful offline forward, ready server and successful physical trial
are different evidence levels. Each detailed guide records its scope; historical
measurements describe their recorded revision rather than certifying this checkout.
An unbound template or unavailable checkpoint is not a working deployment.
