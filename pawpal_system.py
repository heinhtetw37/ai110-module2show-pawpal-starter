from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from enum import Enum


class Priority(Enum):
    # Lower value = scheduled first
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


# How far ahead the next occurrence of a recurring task is due
RECURRENCE_STEP = {
    Frequency.DAILY: timedelta(days=1),
    Frequency.WEEKLY: timedelta(weeks=1),
}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    category: str = "general"  # walk, feeding, meds, enrichment, grooming
    is_completed: bool = False
    time: str | None = None  # fixed start time "HH:MM", or None if flexible
    frequency: Frequency = Frequency.ONCE
    due_date: date = field(default_factory=date.today)
    id: int = 0  # assigned by Pet.add_task

    def __post_init__(self) -> None:
        """Validate priority, duration, frequency, and time after creation."""
        if not isinstance(self.priority, Priority):
            raise ValueError(f"priority must be a Priority, got {self.priority!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if not isinstance(self.frequency, Frequency):
            raise ValueError(f"frequency must be a Frequency, got {self.frequency!r}")
        if self.time is not None:
            try:
                datetime.strptime(self.time, "%H:%M")
            except ValueError:
                raise ValueError(f"time must be HH:MM, got {self.time!r}") from None

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_completed = True

    def next_occurrence(self) -> "Task | None":
        """Return an unfinished copy due on the next date, or None for one-off tasks.

        DAILY tasks move forward 1 day and WEEKLY tasks 7 days, counted from this
        task's due date. This task is not changed, and the copy is not added to any
        pet; Scheduler.complete_task() does that.
        """
        step = RECURRENCE_STEP.get(self.frequency)
        if step is None:
            return None
        # id=0 so Pet.add_task gives the copy its own id
        return replace(self, is_completed=False, due_date=self.due_date + step, id=0)

    def update(self, **changes) -> None:
        """Update one or more fields on this task."""
        for key, value in changes.items():
            if key == "id" or not hasattr(self, key):
                raise AttributeError(f"Task has no editable field {key!r}")
            setattr(self, key, value)
        self.__post_init__()  # re-validate after changes


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)
    _next_id: int = field(default=1, repr=False)

    def add_task(self, task: Task) -> None:
        """Assign the task a unique id (from _next_id) and add it to this pet."""
        task.id = self._next_id
        self._next_id += 1
        self.tasks.append(task)

    def remove_task(self, task_id: int) -> None:
        """Remove the task with the given id."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def edit_task(self, task_id: int, **changes) -> None:
        """Find a task by id and apply the given changes."""
        for task in self.tasks:
            if task.id == task_id:
                task.update(**changes)
                return
        raise KeyError(f"{self.name} has no task with id {task_id}")


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

