"""Optional model-assisted probe proposals.

The deterministic core never requires a provider. Model-generated probes are
labeled MODEL_GENERATED and are never treated as ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from graderprobe.types import ProbeMethod, ProbeSpec, TaskSpec, TransformSpec


@dataclass
class Proposal:
    description: str
    transform: TransformSpec
    rationale: str
    method: ProbeMethod = ProbeMethod.MODEL_GENERATED


class ModelProvider(Protocol):
    name: str

    def propose_probes(self, task: TaskSpec, source: str) -> list[Proposal]:
        ...


class NullProvider:
    """Default provider: no API calls, no proposals."""

    name = "null"

    def propose_probes(self, task: TaskSpec, source: str) -> list[Proposal]:
        return []


def proposals_to_specs(proposals: list[Proposal], *, prefix: str = "MODEL") -> list[ProbeSpec]:
    from graderprobe.types import ExpectedRelation, ProbeClass

    specs: list[ProbeSpec] = []
    for i, proposal in enumerate(proposals, start=1):
        specs.append(
            ProbeSpec(
                id=f"{prefix}-{i:02d}",
                probe_class=ProbeClass.SENSITIVITY,
                description=proposal.description,
                expected_relation=ExpectedRelation.INVALIDATE,
                transform=proposal.transform,
                method=ProbeMethod.MODEL_GENERATED,
                notes=proposal.rationale,
            )
        )
    return specs
