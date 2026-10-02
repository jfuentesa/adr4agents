from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


Identifier = Annotated[int, Field(strict=True, gt=0)]
Page = Annotated[int, Field(strict=True, ge=1, le=1_000_000)]
PageSize = Annotated[int, Field(strict=True, ge=1, le=100)]
DecisionStatus = Literal["draft", "proposed", "accepted", "rejected", "superseded"]
RelationType = Literal["complements", "contradicts", "supersedes"]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProjectInput(InputModel):
    name: str = Field(description="Project name: one word without spaces.")
    description: str = ""
    context: str = ""


class ProjectUpdate(InputModel):
    name: str | None = None
    description: str | None = None
    context: str | None = None


class DecisionScope(InputModel):
    project: str | None = None
    author: str | None = None
    tags: str | None = Field(default=None, description="Comma-separated tags; all must match.")
    date_from: str | None = Field(default=None, description="Inclusive YYYY-MM-DD date.")
    date_to: str | None = Field(default=None, description="Inclusive YYYY-MM-DD date.")


class DecisionFilters(DecisionScope):
    status: DecisionStatus | None = None


class DecisionDraft(InputModel):
    project: str = Field(description="Existing project name: one word without spaces.")
    author: str = Field(description="Alphanumeric author label; no account is required.")
    title: str
    context: str = ""
    alternatives: str = Field(default="", description="Free text, not a list.")
    decision: str = ""
    tags: str = Field(default="", description="Comma-separated words without spaces.")
    date: str | None = Field(default=None, description="YYYY-MM-DD; omit for today's date.")


class DecisionInput(DecisionDraft):
    context: str
    alternatives: str = Field(description="Free text, not a list.")
    decision: str


class DecisionUpdate(InputModel):
    project: str | None = None
    author: str | None = None
    title: str | None = None
    context: str | None = None
    alternatives: str | None = None
    decision: str | None = None
    tags: str | None = Field(default=None, description="Comma-separated words; empty clears tags.")
    date: str | None = Field(default=None, description="YYYY-MM-DD.")


class ReplacementInput(InputModel):
    author: str
    title: str
    context: str = ""
    alternatives: str = ""
    decision: str = ""
    tags: str = ""
    date: str | None = None


class RelationInput(InputModel):
    source_id: Identifier
    target_id: Identifier
    type: RelationType


class RelationUpdate(InputModel):
    source_id: Identifier | None = None
    target_id: Identifier | None = None
    type: RelationType | None = None
