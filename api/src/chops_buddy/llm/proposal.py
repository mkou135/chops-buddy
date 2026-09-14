"""The one structured output the model produces.

Deliberately narrow: the model chooses minutes per target, which targets to defer,
and the words. Mode, tempo, fragment, and threshold are the engine's (E-21) and
are not in this schema, so they cannot be changed by a proposal.
"""

from pydantic import BaseModel, Field


class ProposedSegment(BaseModel):
    target_id: str = Field(description='An assigned target id, or "long_tones".')
    minutes: int = Field(ge=0, le=60)


class Proposal(BaseModel):
    segments: list[ProposedSegment] = Field(
        description="Targets to practise this session, in the order they should be practised."
    )
    deferred: list[str] = Field(
        default_factory=list,
        description="Assigned target ids deliberately left out of this session.",
    )
    rationale: str = Field(
        max_length=800,
        description="One paragraph for the teacher: why this allocation, citing the log.",
    )
    coaching_note: str = Field(
        max_length=200,
        description="One sentence for the student before they start. No points, streaks, badges.",
    )
