"""Pydantic request and response contracts."""

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class Status(StrEnum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


Title = Annotated[str, Field(min_length=1, max_length=200)]
Description = Annotated[str, Field(max_length=5000)]
Owner = Annotated[str, Field(min_length=1, max_length=100)]


def validate_calendar_date(value: object) -> object:
    """Reject timestamps and require the documented date-only input format."""
    if (
        value is not None
        and not isinstance(value, date)
        and (not isinstance(value, str) or len(value) != 10)
    ):
        raise ValueError("Use a calendar date in YYYY-MM-DD format")
    return value


DueDate = Annotated[date, BeforeValidator(validate_calendar_date)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TaskCreate(InputModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Review supplier invoice",
                    "description": "Confirm the total and schedule payment",
                    "owner": "Mariam",
                    "status": "todo",
                    "priority": "high",
                    "due_date": "2026-12-01",
                }
            ]
        }
    )
    title: Title
    description: Description | None = None
    owner: Owner | None = None
    status: Status = Status.todo
    priority: Priority = Priority.medium
    due_date: DueDate | None = None


class TaskUpdate(InputModel):
    title: Title | None = None
    description: Description | None = None
    owner: Owner | None = None
    status: Status | None = None
    priority: Priority | None = None
    due_date: DueDate | None = None

    @model_validator(mode="after")
    def validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")
        for field in ("title", "status", "priority"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    owner: str | None
    status: Status
    priority: Priority
    due_date: date | None
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        return (
            value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        )


class TaskPage(BaseModel):
    items: list[TaskRead]
    total: int
    limit: int
    offset: int
