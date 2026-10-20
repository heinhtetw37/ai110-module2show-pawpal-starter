"""Planning algorithms that turn an Owner's pets and tasks into a daily plan."""

from datetime import date, datetime
from itertools import combinations

from pawpal_system import Owner, Pet, Task


def _to_minutes(hhmm: str | None) -> int | None:
    """Convert an "HH:MM" string to minutes after midnight, or None if it's missing or unreadable."""
    try:
        t = datetime.strptime(hhmm, "%H:%M")
    except (TypeError, ValueError):
        return None
    return t.hour * 60 + t.minute


class Scheduler:
    """Plans all of an owner's pets against one shared time budget."""

    def __init__(self, owner: Owner):
        """Start a scheduler for the given owner with an empty plan."""
        self.owner = owner
        self.scheduled_tasks: list[tuple[Pet, Task]] = []
        self.skipped_tasks: list[tuple[Pet, Task]] = []

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across the owner's pets."""
        return [(pet, task) for pet in self.owner.pets for task in pet.tasks]

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None
    ) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs, optionally limited to one pet and/or a completion status.

        Both filters are optional and combine with AND. Leaving one as None means
        "don't filter on this", so calling with no arguments returns every task.

        Args:
            pet_name: Only include tasks for the pet with this exact name.
            completed: True for finished tasks only, False for unfinished only.

        Returns:
            Matching (pet, task) pairs in the order the pets and tasks were added.
        """
        return [
            (pet, task)
            for pet, task in self.all_tasks()
            if (pet_name is None or pet.name == pet_name)
            and (completed is None or task.is_completed == completed)
        ]

    def sort_by_time(
        self, pairs: list[tuple[Pet, Task]] | None = None
    ) -> list[tuple[Pet, Task]]:
        """Order (pet, task) pairs by fixed start time; tasks without a readable time go last.

        Times are compared as minutes after midnight, not as strings, so "9:30" comes
        before "13:15". Tasks with the same time keep their original order.

        Args:
            pairs: The (pet, task) pairs to sort. Defaults to all of the owner's tasks.

        Returns:
            A new sorted list; the input list is not changed.
        """
        if pairs is None:
            pairs = self.all_tasks()

        def time_key(pt: tuple[Pet, Task]) -> tuple[bool, int]:
            """Sort key: (has no readable time, minutes after midnight)."""
            minutes = _to_minutes(pt[1].time)
            return (minutes is None, minutes or 0)

        return sorted(pairs, key=time_key)

    def complete_task(self, pet: Pet, task_id: int) -> Task | None:
        """Mark a pet's task complete; for daily/weekly tasks, add and return the next occurrence.

        The next occurrence comes from Task.next_occurrence(): an unfinished copy due
        1 day (DAILY) or 7 days (WEEKLY) after this task's due date. It is added to
        the same pet, which gives it a new id.

        Args:
            pet: The pet that owns the task.
            task_id: The id of the task to complete.

        Returns:
            The newly added next occurrence, or None for a one-off (ONCE) task.

        Raises:
            KeyError: If the pet has no task with that id.
        """
        task = next((t for t in pet.tasks if t.id == task_id), None)
        if task is None:
            raise KeyError(f"{pet.name} has no task with id {task_id}")
        task.mark_complete()

        next_task = task.next_occurrence()
        if next_task is not None:
            pet.add_task(next_task)  # gives the new occurrence its own id
        return next_task

    def find_conflicts(self, on: date | None = None) -> list[str]:
        """Return a warning for each pair of unfinished fixed-time tasks (same or different pets) that overlap on a day.

        Algorithm: collect the day's unfinished tasks that have a time, convert each
        to a (start, end) range in minutes, sort by start, then check every pair.
        Two tasks conflict if the later one starts before the earlier one ends, so
        overlapping durations are caught, not just identical start times. A task
        that starts exactly when another ends is not a conflict.

        Lightweight by design: it only reports problems as messages and never raises,
        so a bad time on one task can't crash the app or hide other conflicts.

        Args:
            on: The day to check. Defaults to today.

        Returns:
            Warning strings, empty if there are no conflicts. A task with an
            unreadable time gets a "Warning:" line; each overlapping pair gets a
            "Conflict (same pet|different pets):" line.
        """
        day = on or date.today()
        warnings = []
        timed = []
        for pet, task in self.all_tasks():
            if not task.time or task.is_completed or task.due_date != day:
                continue
            start = _to_minutes(task.time)
            if start is None:
                warnings.append(
                    f"Warning: couldn't check {task.title} ({pet.name}) for conflicts; "
                    f"time {task.time!r} isn't HH:MM."
                )
                continue
            timed.append((start, start + task.duration_minutes, pet, task))
        timed.sort(key=lambda item: item[0])

        # Check every pair. After sorting, the first task in each pair starts no later
        # than the second, so they overlap if the second starts before the first ends.
        for first, second in combinations(timed, 2):
            a_start, a_end, pet_a, a = first
            b_start, _, pet_b, b = second
            if b_start < a_end:
                kind = "same pet" if pet_a is pet_b else "different pets"
                verb = "starts at the same time as" if b_start == a_start else "overlaps"
                warnings.append(
                    f"Conflict ({kind}): {a.title} ({pet_a.name}) at {a.time} {verb} "
                    f"{b.title} ({pet_b.name}) at {b.time}."
                )
        return warnings

    def generate_plan(self, on: date | None = None) -> list[tuple[Pet, Task]]:
        """Choose and order tasks due by the given day (default today) by priority within the owner's available time.

        Greedy algorithm: take every unfinished task due on or before the day, sort
        by priority (HIGH first) and then by duration (shorter first), and add each
        task that still fits in the remaining minutes. Tasks that don't fit are
        skipped, and later, shorter tasks can still fill the leftover time.

        Also stores the results in scheduled_tasks and skipped_tasks, which
        explain_plan() and get_total_duration() read.

        Args:
            on: The day to plan for. Defaults to today.

        Returns:
            The scheduled (pet, task) pairs in the order they should be done.
        """
        day = on or date.today()
        candidates = [
            (pet, task)
            for pet, task in self.all_tasks()
            if not task.is_completed and task.due_date <= day
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
