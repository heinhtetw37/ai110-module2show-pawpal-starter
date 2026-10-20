from dataclasses import dataclass, field
from enum import Enum


class Priority(Enum):
    # Lower value = scheduled first
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    category: str = "general"  # walk, feeding, meds, enrichment, grooming
    is_completed: bool = False
    id: int = 0  # assigned by Pet.add_task

    def __post_init__(self) -> None:
        if not isinstance(self.priority, Priority):
            raise ValueError(f"priority must be a Priority, got {self.priority!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def update(self, **changes) -> None:
        """Update one or more fields on this task."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)
    _next_id: int = field(default=1, repr=False)

    def add_task(self, task: Task) -> None:
        """Assign the task a unique id (from _next_id) and add it to this pet."""
        pass

    def remove_task(self, task_id: int) -> None:
        """Remove the task with the given id."""
        pass

    def edit_task(self, task_id: int, **changes) -> None:
        """Find a task by id and apply the given changes."""
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        pass


class Scheduler:
    """Plans all of an owner's pets against one shared time budget."""

    def __init__(self, owner: Owner):
        self.owner = owner
        self.scheduled_tasks: list[tuple[Pet, Task]] = []
        self.skipped_tasks: list[tuple[Pet, Task]] = []

    def generate_plan(self) -> list[tuple[Pet, Task]]:
        """Choose and order tasks from every pet by priority within the owner's available time."""
        pass

    def explain_plan(self) -> str:
        """Explain why each task was scheduled or skipped."""
        pass

    def get_total_duration(self) -> int:
        """Return the total minutes of scheduled tasks."""
        pass
