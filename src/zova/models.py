"""Validated inputs. All times represent aware instants; money uses Decimal."""

from datetime import timedelta
from decimal import Decimal
from typing import Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TimeWindow(Model):
    start: AwareDatetime
    end: AwareDatetime

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.end <= self.start:
            raise ValueError("Time window must end after it starts")
        return self


class TravelerProfile(Model):
    name: str
    destination: str
    budget: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: Literal["USD"] = "USD"
    preferences: tuple[str, ...]
    trip: TimeWindow
    unavailable: tuple[TimeWindow, ...] = ()


class Activity(Model):
    id: str
    title: str
    destination: str
    categories: tuple[str, ...]
    cost: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: Literal["USD"] = "USD"
    duration_minutes: int = Field(gt=0)
    schedule: TimeWindow
    source: Literal["synthetic fixture"] = "synthetic fixture"

    @model_validator(mode="after")
    def duration_matches(self) -> Self:
        if self.schedule.end - self.schedule.start != timedelta(minutes=self.duration_minutes):
            raise ValueError("Duration must match the scheduled session")
        return self


class Itinerary(Model):
    activities: tuple[Activity, ...]

    @property
    def total_cost(self) -> Decimal:
        return sum((activity.cost for activity in self.activities), Decimal("0.00"))
