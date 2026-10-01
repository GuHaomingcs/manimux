# Viewer body configuration

The live YAM and Tianji dashboards load their `viewer.yaml` through the generic
`RobotView` and the assembled offline `RobotModel`. Add a new body with a model
reference, camera slots and display styling. Do not duplicate its FK/IK in a
per-robot Python display adapter.

`base.py`, `yam.py` and the old discovery exports remain for compatibility
consumers, including historical collection-record replay. They are not the live
dashboard integration path. See the [display protocol](../../../docs/development/runtime-config.md#viewer-replay-and-recording).
