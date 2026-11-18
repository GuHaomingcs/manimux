from __future__ import annotations

import json
import math
import time
import uuid
from pathlib import Path

import numpy as np

from manimux.policies.capabilities import PolicyCapabilities
from manimux.policy_adapter.base import PolicyAdapter
from manimux.types import ActionChunk, ActionContext, InferenceRequest, ObservationSnapshot


class FakePolicyAdapter(PolicyAdapter):
    def build_observation(self, snapshot: ObservationSnapshot) -> ObservationSnapshot:
        return snapshot

    def decode_action(self, raw: object, context: ActionContext) -> ActionChunk:
        del context
        if not isinstance(raw, ActionChunk):
            raise TypeError("identity adapter requires an ActionChunk")
        return raw

    def validate(self, robot: dict, policy: dict) -> None:
        if not robot["group_dims"]:
            raise ValueError("fake policy requires robot groups")
        if policy["horizon_policy_steps"] < 2:
            raise ValueError("fake policy requires at least two horizon steps")


def read_delay_trace(path: Path) -> list[float]:
    """Recover one worker measurement per request, in submission order."""
    samples = {}
    with path.open(encoding="utf-8") as events:
        for line in events:
            event = json.loads(line)
            if event["kind"] != "inference_response":
                continue
            if event.get("error") == "deadline_exceeded_before_start":
                continue
            seq = event["request_seq"]
            if type(seq) is not int or seq < 1 or seq in samples:
                raise ValueError(f"invalid or duplicate inference request {seq!r} in {path}")
            samples[seq] = event["inference_ms"]
    if not samples:
        raise ValueError(f"no per-request inference measurements in {path}")
    return [samples[seq] for seq in sorted(samples)]


class FakePolicyModel:
    def __init__(
        self,
        action_dt_ns: int,
        horizon_steps: int,
        delay_s: float,
        *,
        delay_trace_ms: list[float] | None = None,
    ) -> None:
        if delay_trace_ms is not None and (
            not isinstance(delay_trace_ms, list)
            or not delay_trace_ms
            or any(
                type(ms) not in (int, float) or not math.isfinite(ms) or ms < 0
                for ms in delay_trace_ms
            )
        ):
            raise ValueError(
                "delay_trace_ms must be a nonempty list of finite nonnegative milliseconds"
            )
        self._delay_trace_ms = delay_trace_ms
        self._action_dt_ns = action_dt_ns
        self._horizon_steps = horizon_steps
        self._delay_s = delay_s
        self._session_id: str | None = None

    def reset(self, session_id: str) -> None:
        self._session_id = session_id

    def infer(self, request: InferenceRequest) -> ActionChunk:
        if request.session_id != self._session_id:
            raise RuntimeError("fake policy session is not initialized")
        delay_s = self._delay_s
        metadata: dict[str, object] = {}
        if self._delay_trace_ms is not None:
            # Preview encodes its zero-based sequence as -(seq + 1). It may run
            # longer than one trace; the formal rollout always starts at index zero.
            seq = request.request_seq
            index = (-seq - 1) % len(self._delay_trace_ms) if seq < 0 else seq - 1
            delay_ms = self._delay_trace_ms[index]
            delay_s = delay_ms / 1000
            metadata["replay_delay_ms"] = delay_ms
        if delay_s:
            time.sleep(delay_s)
        phase = request.request_seq * 0.35
        step_axis = np.linspace(0.0, 1.0, self._horizon_steps, dtype=np.float64)
        groups: dict[str, np.ndarray] = {}
        for group_name, current in request.observation.state.groups.items():
            amplitude = 0.12 if "arm" in group_name else 0.04
            direction = -1.0 if group_name.startswith("right") else 1.0
            wave = direction * amplitude * np.sin(phase + step_axis * np.pi)
            groups[group_name] = current[None, :] + wave[:, None]
        now_ns = time.monotonic_ns()
        return ActionChunk(
            plan_id=f"plan-{request.request_seq}-{uuid.uuid4().hex[:8]}",
            request_seq=request.request_seq,
            observation_time_ns=request.observation_time_ns,
            created_time_ns=now_ns,
            action_space="joint_position",
            dt_ns=self._action_dt_ns,
            groups=groups,
            metadata=metadata,
        )

    def capabilities(self) -> PolicyCapabilities:
        return PolicyCapabilities(
            sampling_modes=frozenset({"default", "rtc"}),
            request_limit=None if self._delay_trace_ms is None else len(self._delay_trace_ms),
        )

    def close(self) -> None:
        self._session_id = None
