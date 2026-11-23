"""Compare the Serial and Async demo schedules on a planar tracking task."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from manimux.cli import load_config
from manimux.policies.fake import FakePolicyAdapter
from manimux.runtime.executors.direct import DirectExecutor
from manimux.runtime.inference import build_inference_strategy
from manimux.runtime.preview import PreviewPlanner
from manimux.runtime.safety import SafetyGuard
from manimux.types import (
    ActionChunk,
    FloatArray,
    InferenceRequest,
    InferenceResponse,
    ObservationSnapshot,
    RobotState,
)

DEMO = Path(__file__).resolve().parents[2] / "manimux/configs/experiments/example-synthetic/demo"
RADIUS_M = 0.1
PLANT_TIME_CONSTANT_S = 0.1
REACH_SPEED_M_S = 0.4


class SimulationClock:
    time_ns = 0

    def now_ns(self) -> int:
        return self.time_ns


def predict(
    request: InferenceRequest, target: FloatArray, delay_ms: float, policy: dict[str, Any]
) -> InferenceResponse:
    """Move to the observed target over the chunk, with no access to future target positions."""
    start = request.observation.state.groups["xy"]
    ready_ns = request.observation_time_ns + round(delay_ms * 1e6)
    offset = target - start
    distance = float(np.linalg.norm(offset))
    travel = np.arange(policy["horizon_policy_steps"]) * policy["action_dt_s"] * REACH_SPEED_M_S
    fraction = np.minimum(travel / distance, 1.0) if distance else np.zeros_like(travel)
    chunk = ActionChunk(
        plan_id=f"plan-{request.request_seq}",
        request_seq=request.request_seq,
        observation_time_ns=request.observation_time_ns,
        created_time_ns=ready_ns,
        action_space="joint_position",
        dt_ns=round(policy["action_dt_s"] * 1e9),
        groups={"xy": start + fraction[:, None] * offset},
    )
    return InferenceResponse(
        session_id=request.session_id,
        request_seq=request.request_seq,
        observation_time_ns=request.observation_time_ns,
        deadline_ns=request.deadline_ns,
        finished_time_ns=ready_ns,
        inference_ms=delay_ms,
        raw_action=chunk,
    )


def run(
    method: str, delays_ms: list[float], duration_s: float, speed_m_s: float, tolerance_m: float
) -> dict[str, str | float | int]:
    config = load_config(DEMO / f"{method}.yaml")
    config["robot"]["group_dims"] = {"xy": 2}
    clock = SimulationClock()
    strategy = build_inference_strategy(config)
    planner = PreviewPlanner(
        config,
        strategy=strategy,
        adapter=FakePolicyAdapter(config["robot"], config["policy"]),
        executor=DirectExecutor(),
        kinematics=None,
        safety=SafetyGuard({"xy": 2}, position_limit_abs=None),
        decoder=None,
        session_id=method,
        clock=clock,
    )
    dt_ns = round(1e9 / config["robot"]["control_hz"])
    duration_ns = round(duration_s * 1e9)
    position = np.array([RADIUS_M, 0.0])
    pending = None
    squared_error_time = 0.0
    outside_ns = requests = accepted = rejected = 0
    for step, now_ns in enumerate(range(0, duration_ns, dt_ns)):
        clock.time_ns = now_ns
        interval_ns = min(dt_ns, duration_ns - now_ns)
        angle = now_ns / 1e9 * speed_m_s / RADIUS_M
        target = RADIUS_M * np.array([math.cos(angle), math.sin(angle)])
        # Left-endpoint sampling includes startup and holds and weights the last partial tick.
        error_sq = float(np.sum((position - target) ** 2))
        squared_error_time += error_sq * interval_ns
        if error_sq > tolerance_m**2:
            outside_ns += interval_ns

        state = RobotState({"xy": position}, now_ns, step)
        planner.initialize(state)
        if pending is not None and pending.finished_time_ns <= now_ns:
            reason = planner.rejection_reason(pending)
            if reason is None:
                _, result, _ = planner.accept(pending.raw_action, pending, state)
                reason = None if result.accepted else result.reason
            if reason is None:
                accepted += 1
            else:
                pending.error = reason
                strategy.on_response_rejected(pending)
                rejected += 1
            pending = None

        submission = planner.submission(
            ObservationSnapshot(state, {}), in_flight=pending is not None
        )
        if submission is not None:
            request = submission.request
            pending = predict(
                request, target, delays_ms[requests % len(delays_ms)], config["policy"]
            )
            planner.submitted(request, now_ns)
            requests += 1

        planner.tick(state, loop_started_ns=now_ns)
        gain = -math.expm1(-interval_ns / 1e9 / PLANT_TIME_CONSTANT_S)
        assert planner.last_command is not None
        position = position + gain * (planner.last_command["xy"] - position)

    return {
        "method": method,
        "tracking_rmse_mm": 1000 * math.sqrt(squared_error_time / duration_ns),
        "outside_tolerance_s": outside_ns / 1e9,
        "requests": requests,
        "accepted": accepted,
        "rejected": rejected,
        "pending": int(pending is not None),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--delay-ms",
        type=float,
        nargs="+",
        default=[100.0],
        help="Inference delay pattern in milliseconds, repeated in request order",
    )
    parser.add_argument("--duration-s", type=float, default=12.0)
    parser.add_argument("--speed-m-s", type=float, default=0.1)
    parser.add_argument("--tolerance-mm", type=float, default=30.0)
    args = parser.parse_args()
    values = [args.duration_s, args.speed_m_s, args.tolerance_mm, *args.delay_ms]
    if not all(math.isfinite(x) and x >= 0 for x in values) or round(args.duration_s * 1e9) < 1:
        parser.error("use finite nonnegative inputs and a duration of at least one nanosecond")
    results = [
        run(method, args.delay_ms, args.duration_s, args.speed_m_s, args.tolerance_mm / 1000)
        for method in ("serial", "async")
    ]
    print(json.dumps({**vars(args), "results": results}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
