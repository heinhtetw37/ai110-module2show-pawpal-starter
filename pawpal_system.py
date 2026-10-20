from dataclasses import dataclass, field


@dataclass
class Task:
    id: int
    title: str
    duration_minutes: int
    priority: str = "medium"  # high / medium / low
    category: str = "general"  # walk, feeding, meds, enrichment, grooming
    is_completed: bool = False

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

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
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
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.scheduled_tasks: list[Task] = []
        self.skipped_tasks: list[Task] = []

    def generate_plan(self) -> list[Task]:
        """Choose and order tasks by priority within the owner's available time."""
        pass

    def explain_plan(self) -> str:
        """Explain why each task was scheduled or skipped."""
        pass

    def get_total_duration(self) -> int:
        """Return the total minutes of scheduled tasks."""
        pass
