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
        """Validate priority and duration after creation."""
        if not isinstance(self.priority, Priority):
            raise ValueError(f"priority must be a Priority, got {self.priority!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_completed = True

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


class Scheduler:
    """Plans all of an owner's pets against one shared time budget."""

    def __init__(self, owner: Owner):
        """Start a scheduler for the given owner with an empty plan."""
        self.owner = owner
        self.scheduled_tasks: list[tuple[Pet, Task]] = []
        self.skipped_tasks: list[tuple[Pet, Task]] = []

    def generate_plan(self) -> list[tuple[Pet, Task]]:
        """Choose and order tasks from every pet by priority within the owner's available time."""
        candidates = [
            (pet, task)
            for pet in self.owner.pets
            for task in pet.tasks
            if not task.is_completed
        ]
        # Highest priority first; shorter tasks first to break ties
        candidates.sort(key=lambda pt: (pt[1].priority.value, pt[1].duration_minutes))

        self.scheduled_tasks = []
        self.skipped_tasks = []
        remaining = self.owner.available_minutes
        for pet, task in candidates:
            if task.duration_minutes <= remaining:
                self.scheduled_tasks.append((pet, task))
                remaining -= task.duration_minutes
            else:
                self.skipped_tasks.append((pet, task))
        return self.scheduled_tasks

    def explain_plan(self) -> str:
        """Explain why each task was scheduled or skipped."""
        lines = []
        for pet, task in self.scheduled_tasks:
            lines.append(
                f"Scheduled {task.title} ({pet.name}): {task.priority.name} priority, "
                f"{task.duration_minutes} min fits in the time budget."
            )
        for pet, task in self.skipped_tasks:
            lines.append(
                f"Skipped {task.title} ({pet.name}): {task.duration_minutes} min "
                f"did not fit in the remaining time."
            )
        return "\n".join(lines)

    def get_total_duration(self) -> int:
        """Return the total minutes of scheduled tasks."""
        return sum(task.duration_minutes for _, task in self.scheduled_tasks)
