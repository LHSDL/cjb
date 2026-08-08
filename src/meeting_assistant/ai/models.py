"""千问原始输出的数据契约。"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceReference(StrictModel):
    line_id: Annotated[str, StringConstraints(pattern=r"^L\d{3,}$")]
    quote: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ]


class RawDecision(StrictModel):
    content: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ]
    sources: list[SourceReference] = Field(min_length=1, max_length=10)


class RawActionSuggestion(StrictModel):
    content: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ]
    owner: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ] | None
    due_date_expression: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
    ] | None
    sources: list[SourceReference] = Field(min_length=1, max_length=10)


class RawAnalysis(StrictModel):
    summary: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)
    ]
    decisions: list[RawDecision] = Field(default_factory=list, max_length=20)
    action_items: list[RawActionSuggestion] = Field(
        default_factory=list, max_length=20
    )
    security_warnings: list[
        Annotated[
            str,
            StringConstraints(strip_whitespace=True, min_length=1, max_length=300),
        ]
    ] = Field(default_factory=list, max_length=20)


class ActionSuggestion(StrictModel):
    content: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ]
    owner: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ] | None
    owner_needs_confirmation: bool
    due_date_expression: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
    ] | None
    due_date: Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}$")] | None
    due_date_needs_confirmation: bool
    sources: list[SourceReference] = Field(min_length=1, max_length=20)
    warnings: list[
        Annotated[
            str,
            StringConstraints(strip_whitespace=True, min_length=1, max_length=300),
        ]
    ] = Field(default_factory=list, max_length=20)


class AIAnalysis(StrictModel):
    model: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ]
    summary: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)
    ]
    decisions: list[RawDecision] = Field(default_factory=list, max_length=20)
    action_items: list[ActionSuggestion] = Field(default_factory=list, max_length=20)
    security_warnings: list[
        Annotated[
            str,
            StringConstraints(strip_whitespace=True, min_length=1, max_length=300),
        ]
    ] = Field(default_factory=list, max_length=40)

