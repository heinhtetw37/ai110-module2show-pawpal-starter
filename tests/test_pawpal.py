from datetime import date

import pytest

from pawpal_system import Frequency, Pet, Priority, Task


def test_mark_complete_changes_status():
    """mark_complete() should flip is_completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30)
    assert task.is_completed is False

    task.mark_complete()

    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    """add_task() should increase the pet's task count by one."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Feed breakfast", duration_minutes=10))

    assert len(pet.tasks) == 1


def test_next_occurrence_follows_frequency():
    """next_occurrence() moves the due date by the task's frequency and doesn't change the original."""
    start = date(2026, 10, 19)
    daily = Task("Breakfast", 10, frequency=Frequency.DAILY, due_date=start, id=4)
    weekly = Task("Bath", 30, frequency=Frequency.WEEKLY, due_date=start)
    daily.mark_complete()

    next_daily = daily.next_occurrence()

    assert next_daily.due_date == date(2026, 10, 20)
    assert next_daily.is_completed is False
    assert next_daily.id == 0  # Pet.add_task assigns the real id
    assert next_daily.title == "Breakfast"
    assert daily.is_completed is True and daily.due_date == start
    assert weekly.next_occurrence().due_date == date(2026, 10, 26)


def test_next_occurrence_is_none_for_one_off_task():
    """A ONCE task has no next occurrence."""
    assert Task("Vet visit", 60).next_occurrence() is None


def make_pet_with_tasks(*titles: str) -> Pet:
    """Build a pet with one 10-minute task per title."""
    pet = Pet(name="Mochi", species="dog")
    for title in titles:
        pet.add_task(Task(title, 10))
    return pet


# --- Validation on creation ---


@pytest.mark.parametrize(
    "kwargs",
    [
        {"priority": "high"},
        {"duration_minutes": 0},
        {"duration_minutes": -5},
        {"frequency": "daily"},
        {"time": "8am"},
        {"time": "25:00"},
    ],
    ids=["priority-string", "zero-duration", "negative-duration", "frequency-string",
         "time-8am", "time-25:00"],
)
def test_invalid_task_is_rejected(kwargs):
    """Each kind of invalid value raises ValueError when the task is created."""
    fields = {"title": "Walk", "duration_minutes": 30, **kwargs}
    with pytest.raises(ValueError):
        Task(**fields)


def test_valid_task_uses_defaults():
    """A task with only a title and duration gets sensible defaults."""
    task = Task("Walk", 30)

    assert task.priority is Priority.MEDIUM
    assert task.frequency is Frequency.ONCE
    assert task.time is None
    assert task.is_completed is False
    assert task.due_date == date.today()


# --- Unique ids ---


def test_add_task_assigns_increasing_ids():
    """Each added task gets the next id, starting at 1."""
    pet = make_pet_with_tasks("A", "B", "C")

    assert [t.id for t in pet.tasks] == [1, 2, 3]


def test_ids_are_not_reused_after_removal():
    """Removing a task doesn't free its id for the next task."""
    pet = make_pet_with_tasks("A", "B")
    pet.remove_task(2)
    pet.add_task(Task("C", 10))

    assert [t.id for t in pet.tasks] == [1, 3]


def test_ids_are_per_pet():
    """Each pet counts its own ids, so two pets can both have task 1."""
    mochi = make_pet_with_tasks("Walk")
    luna = Pet(name="Luna", species="cat")
    luna.add_task(Task("Meds", 5))

    assert mochi.tasks[0].id == 1
    assert luna.tasks[0].id == 1


# --- Editing ---


def test_edit_task_changes_only_that_task():
    """edit_task updates the matching task and leaves the others alone."""
    pet = make_pet_with_tasks("Walk", "Breakfast")

    pet.edit_task(1, title="Evening walk", priority=Priority.HIGH)

    assert pet.tasks[0].title == "Evening walk"
    assert pet.tasks[0].priority is Priority.HIGH
    assert pet.tasks[1].title == "Breakfast"


def test_edit_task_unknown_id_raises():
    """Editing a task id the pet doesn't have raises KeyError."""
    pet = make_pet_with_tasks("Walk")
    with pytest.raises(KeyError):
        pet.edit_task(99, title="Nope")


@pytest.mark.parametrize("field_name", ["id", "colour"])
def test_update_refuses_id_and_unknown_fields(field_name):
    """update() refuses to change the id or a field that doesn't exist."""
    task = Task("Walk", 30, id=1)
    with pytest.raises(AttributeError):
        task.update(**{field_name: 5})
    assert task.id == 1


def test_update_rejects_invalid_value():
    """update() re-validates, so an invalid new value raises ValueError."""
    task = Task("Walk", 30)
    with pytest.raises(ValueError):
        task.update(duration_minutes=-5)


def test_failed_update_leaves_task_unchanged():
    """A rejected update leaves every field at its old value, even ones that were valid."""
    task = Task("Walk", 30, time="08:00")
    with pytest.raises(ValueError):
        task.update(duration_minutes=-5)
    with pytest.raises(ValueError):
        task.update(title="Long walk", time="8am")

    assert task.duration_minutes == 30
    assert task.time == "08:00"
    assert task.title == "Walk"


def test_update_refuses_method_names():
    """update() only changes data fields, so it can't overwrite a method like mark_complete."""
    task = Task("Walk", 30)
    with pytest.raises(AttributeError):
        task.update(mark_complete=5)

    task.mark_complete()
    assert task.is_completed is True


# --- Removing ---


def test_remove_task_removes_only_that_task():
    """remove_task drops the matching task and keeps the rest in order."""
    pet = make_pet_with_tasks("A", "B", "C")

    pet.remove_task(2)

    assert [t.title for t in pet.tasks] == ["A", "C"]


def test_remove_task_unknown_id_does_nothing():
    """Current behavior: removing an unknown id is silently ignored (unlike edit_task)."""
    pet = make_pet_with_tasks("A", "B")

    pet.remove_task(99)

    assert [t.title for t in pet.tasks] == ["A", "B"]
