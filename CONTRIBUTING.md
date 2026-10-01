# Contributing

Start with the [integration map](docs/development/README.md). Choose the existing
interface that owns your change and include a selecting configuration, a runnable
example and focused validation. A supported method/robot entry must state what was
actually checked: configuration, offline inference or real-robot operation.

Coding agents should read [AGENTS.md](AGENTS.md) and the matching repository skill.
Humans can use the same [protocol guides](docs/development/README.md) directly.

Keep model dependencies in their owning framework, device bindings in a private
station file, and research settings in YAML. Preserve a checkpoint's action meaning,
normalization and sampling requirements. New comments and general documentation
are English; maintain both homepage languages when changing user-facing behavior.

Do not commit recordings, weights, local credentials or hardware addresses.
Regression checks currently live in the ignored local `tests/` workspace; include
the commands and results in your change description rather than force-adding tests.
Submit a focused change that explains the user-visible behavior, interface/config
changes, validation performed and remaining hardware or checkpoint requirements.
