from datetime import date, timedelta

import pytest

from pawpal_system import Frequency, Owner, Pet, Task
from scheduler import Scheduler

TODAY = date(2026, 10, 19)


def make_scheduler(*pets: Pet) -> Scheduler:
    """Build a scheduler for an owner with the given pets and a 90-minute budget."""
    owner = Owner(name="Jordan", available_minutes=90)
    for pet in pets:
        owner.add_pet(pet)
    return Scheduler(owner)


def test_sort_by_time_orders_by_clock_and_puts_untimed_last():
    """Times are compared as clock times, not strings, and untimed tasks go last."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Dinner", 10, time="13:15"))
    pet.add_task(Task("Brush coat", 20))
    pet.add_task(Task("Breakfast", 10, time="9:30"))
    pet.add_task(Task("Morning walk", 30, time="08:00"))

    titles = [t.title for _, t in make_scheduler(pet).sort_by_time()]

    assert titles == ["Morning walk", "Breakfast", "Dinner", "Brush coat"]


def test_filter_tasks_by_pet_and_status():
    """filter_tasks can narrow by pet name, completion status, or both."""
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    mochi.add_task(Task("Walk", 30))
    mochi.add_task(Task("Breakfast", 10, is_completed=True))
    luna.add_task(Task("Give meds", 5))
    scheduler = make_scheduler(mochi, luna)

    assert [t.title for _, t in scheduler.filter_tasks(pet_name="Mochi")] == ["Walk", "Breakfast"]
    assert [t.title for _, t in scheduler.filter_tasks(completed=False)] == ["Walk", "Give meds"]
    assert [t.title for _, t in scheduler.filter_tasks(pet_name="Mochi", completed=True)] == ["Breakfast"]
    assert scheduler.filter_tasks(pet_name="Rex") == []


@pytest.mark.parametrize(
    "frequency, step", [(Frequency.DAILY, timedelta(days=1)), (Frequency.WEEKLY, timedelta(weeks=1))]
)
def test_completing_recurring_task_creates_next_occurrence(frequency, step):
    """A daily/weekly task comes back as a new, unfinished task on its next due date."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Breakfast", 10, frequency=frequency, due_date=TODAY))
    scheduler = make_scheduler(pet)

    next_task = scheduler.complete_task(pet, task_id=1)

    assert pet.tasks[0].is_completed is True
    assert next_task in pet.tasks
    assert next_task.is_completed is False
    assert next_task.due_date == TODAY + step
    assert next_task.id == 2
    assert next_task.title == "Breakfast"


def test_completing_one_off_task_does_not_recur():
    """A ONCE task is just marked complete; nothing new is added."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Vet visit", 60, due_date=TODAY))

    assert make_scheduler(pet).complete_task(pet, task_id=1) is None
    assert len(pet.tasks) == 1
    assert pet.tasks[0].is_completed is True


def test_complete_task_unknown_id_raises():
    """Completing a task id the pet doesn't have raises KeyError."""
    pet = Pet(name="Mochi", species="dog")
    with pytest.raises(KeyError):
        make_scheduler(pet).complete_task(pet, task_id=99)


def test_generate_plan_skips_tasks_due_in_the_future():
    """Tomorrow's occurrence of a recurring task is not planned for today."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Breakfast", 10, frequency=Frequency.DAILY, due_date=TODAY))
    scheduler = make_scheduler(pet)
    scheduler.complete_task(pet, task_id=1)

    assert scheduler.generate_plan(on=TODAY) == []
    assert [t.due_date for _, t in scheduler.generate_plan(on=TODAY + timedelta(days=1))] == [
        TODAY + timedelta(days=1)
    ]


def test_find_conflicts_reports_overlaps_across_pets():
    """Overlapping fixed-time tasks conflict, even for different pets."""
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    mochi.add_task(Task("Breakfast", 10, time="08:00", due_date=TODAY))
    luna.add_task(Task("Give meds", 5, time="08:05", due_date=TODAY))

    conflicts = make_scheduler(mochi, luna).find_conflicts(on=TODAY)

    assert conflicts == [
        "Conflict (different pets): Breakfast (Mochi) at 08:00 overlaps Give meds (Luna) at 08:05."
    ]


def test_find_conflicts_same_start_time_same_pet():
    """Two tasks for one pet at the exact same time are flagged as a same-pet conflict."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, time="08:00", due_date=TODAY))
    pet.add_task(Task("Breakfast", 10, time="08:00", due_date=TODAY))

    conflicts = make_scheduler(pet).find_conflicts(on=TODAY)

    assert conflicts == [
        "Conflict (same pet): Walk (Mochi) at 08:00 starts at the same time as "
        "Breakfast (Mochi) at 08:00."
    ]


def test_find_conflicts_same_start_time_different_pets():
    """Same start time across pets is caught, even when one time has no leading zero."""
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    mochi.add_task(Task("Breakfast", 10, time="08:00", due_date=TODAY))
    luna.add_task(Task("Give meds", 5, time="8:00", due_date=TODAY))
    luna.add_task(Task("Play", 10, time="12:00", due_date=TODAY))

    conflicts = make_scheduler(mochi, luna).find_conflicts(on=TODAY)

    assert conflicts == [
        "Conflict (different pets): Breakfast (Mochi) at 08:00 starts at the same time as "
        "Give meds (Luna) at 8:00."
    ]


def test_find_conflicts_ignores_back_to_back_tasks():
    """A task that starts exactly when another ends is not a conflict."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, time="08:00", due_date=TODAY))
    pet.add_task(Task("Breakfast", 10, time="08:30", due_date=TODAY))

    assert make_scheduler(pet).find_conflicts(on=TODAY) == []


def test_find_conflicts_catches_overlap_with_non_neighbor():
    """A long task can overlap several later tasks, not just the next one."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Long walk", 60, time="08:00", due_date=TODAY))
    pet.add_task(Task("Breakfast", 10, time="08:10", due_date=TODAY))
    pet.add_task(Task("Give meds", 5, time="08:30", due_date=TODAY))

    conflicts = make_scheduler(pet).find_conflicts(on=TODAY)

    assert len(conflicts) == 2
    assert all(c.startswith("Conflict (same pet): Long walk") for c in conflicts)


def test_find_conflicts_ignores_completed_and_other_days():
    """Completed tasks and tasks due on other days don't count as conflicts."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, time="08:00", due_date=TODAY))
    pet.add_task(Task("Breakfast", 10, time="08:10", due_date=TODAY, is_completed=True))
    pet.add_task(Task("Groom", 20, time="08:10", due_date=TODAY + timedelta(days=1)))

    assert make_scheduler(pet).find_conflicts(on=TODAY) == []


def test_bad_time_gives_warning_instead_of_crashing():
    """A time set directly to bad text produces a warning; other conflicts are still found."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, time="08:00", due_date=TODAY))
    pet.add_task(Task("Breakfast", 10, time="08:10", due_date=TODAY))
    bad = Task("Give meds", 5, time="09:00", due_date=TODAY)
    pet.add_task(bad)
    bad.time = "8am"  # bypasses Task validation
    scheduler = make_scheduler(pet)

    conflicts = scheduler.find_conflicts(on=TODAY)

    assert conflicts == [
        "Warning: couldn't check Give meds (Mochi) for conflicts; time '8am' isn't HH:MM.",
        "Conflict (same pet): Walk (Mochi) at 08:00 overlaps Breakfast (Mochi) at 08:10.",
    ]
    # sort_by_time treats the unreadable time like a missing one: last, no crash
    assert [t.title for _, t in scheduler.sort_by_time()] == ["Walk", "Breakfast", "Give meds"]


def test_invalid_time_is_rejected():
    """A time that isn't HH:MM raises ValueError."""
    with pytest.raises(ValueError):
        Task("Walk", 30, time="8am")
