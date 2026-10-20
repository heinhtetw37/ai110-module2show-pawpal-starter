from datetime import date

from pawpal_system import Frequency, Pet, Task


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
