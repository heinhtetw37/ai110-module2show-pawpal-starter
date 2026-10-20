from datetime import date, timedelta

import pytest

from pawpal_system import Frequency, Owner, Pet, Priority, Task
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


def test_completing_daily_task_creates_task_for_next_day():
    """Marking a daily task complete adds a new, unfinished copy due the following day."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Breakfast", 10, frequency=Frequency.DAILY, due_date=TODAY))
    scheduler = make_scheduler(pet)

    next_task = scheduler.complete_task(pet, task_id=1)

    assert pet.tasks[0].is_completed is True
    assert len(pet.tasks) == 2
    assert next_task in pet.tasks
    assert next_task.is_completed is False
    assert next_task.due_date == TODAY + timedelta(days=1)
    assert next_task.id == 2
    assert next_task.title == "Breakfast"


def test_completing_weekly_task_creates_task_for_next_week():
    """Marking a weekly task complete adds a new, unfinished copy due 7 days later."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Bath", 30, frequency=Frequency.WEEKLY, due_date=TODAY))

    next_task = make_scheduler(pet).complete_task(pet, task_id=1)

    assert pet.tasks[0].is_completed is True
    assert next_task in pet.tasks
    assert next_task.is_completed is False
    assert next_task.due_date == TODAY + timedelta(weeks=1)


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


# --- Planning ---


def test_generate_plan_orders_by_priority_then_shortest():
    """HIGH tasks come first, and shorter tasks break ties within a priority."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Brush coat", 20, priority=Priority.LOW, due_date=TODAY))
    pet.add_task(Task("Long walk", 30, priority=Priority.HIGH, due_date=TODAY))
    pet.add_task(Task("Give meds", 5, priority=Priority.HIGH, due_date=TODAY))
    pet.add_task(Task("Play", 15, due_date=TODAY))

    titles = [t.title for _, t in make_scheduler(pet).generate_plan(on=TODAY)]

    assert titles == ["Give meds", "Long walk", "Play", "Brush coat"]


def test_generate_plan_skips_tasks_that_dont_fit_and_fills_leftover_time():
    """A task too long for the remaining time is skipped, but a later shorter one can still fit."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Long walk", 60, priority=Priority.HIGH, due_date=TODAY))
    pet.add_task(Task("Vet visit", 45, priority=Priority.MEDIUM, due_date=TODAY))
    pet.add_task(Task("Brush coat", 20, priority=Priority.LOW, due_date=TODAY))
    scheduler = make_scheduler(pet)  # 90-minute budget

    plan = scheduler.generate_plan(on=TODAY)

    assert [t.title for _, t in plan] == ["Long walk", "Brush coat"]
    assert [t.title for _, t in scheduler.skipped_tasks] == ["Vet visit"]
    assert scheduler.get_total_duration() == 80


def test_generate_plan_task_exactly_filling_budget_is_scheduled():
    """A task whose duration equals the remaining minutes still fits."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Long walk", 90, due_date=TODAY))
    scheduler = make_scheduler(pet)

    assert len(scheduler.generate_plan(on=TODAY)) == 1
    assert scheduler.skipped_tasks == []


def test_generate_plan_shares_one_budget_across_pets():
    """All pets draw from the owner's single time budget."""
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    mochi.add_task(Task("Long walk", 60, priority=Priority.HIGH, due_date=TODAY))
    luna.add_task(Task("Play", 40, priority=Priority.HIGH, due_date=TODAY))
    scheduler = make_scheduler(mochi, luna)

    plan = scheduler.generate_plan(on=TODAY)

    assert [(p.name, t.title) for p, t in plan] == [("Luna", "Play")]
    assert [(p.name, t.title) for p, t in scheduler.skipped_tasks] == [("Mochi", "Long walk")]


def test_generate_plan_excludes_completed_but_includes_overdue():
    """Finished tasks are left out; unfinished tasks from earlier days are still planned."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Breakfast", 10, due_date=TODAY, is_completed=True))
    pet.add_task(Task("Trim nails", 15, due_date=TODAY - timedelta(days=2)))

    titles = [t.title for _, t in make_scheduler(pet).generate_plan(on=TODAY)]

    assert titles == ["Trim nails"]


def test_generate_plan_resets_previous_results():
    """Running the plan again replaces the old scheduled/skipped lists instead of adding to them."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, due_date=TODAY))
    pet.add_task(Task("Vet visit", 120, due_date=TODAY))
    scheduler = make_scheduler(pet)

    scheduler.generate_plan(on=TODAY)
    scheduler.generate_plan(on=TODAY)

    assert len(scheduler.scheduled_tasks) == 1
    assert len(scheduler.skipped_tasks) == 1


def test_generate_plan_with_no_tasks_is_empty():
    """An owner with no pets or tasks gets an empty plan and zero minutes."""
    scheduler = make_scheduler()

    assert scheduler.generate_plan(on=TODAY) == []
    assert scheduler.get_total_duration() == 0
    assert scheduler.explain_plan() == ""


def test_explain_plan_mentions_scheduled_and_skipped_tasks():
    """Each scheduled and skipped task gets one line explaining why."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Give meds", 5, priority=Priority.HIGH, due_date=TODAY))
    pet.add_task(Task("Vet visit", 120, due_date=TODAY))
    scheduler = make_scheduler(pet)
    scheduler.generate_plan(on=TODAY)

    assert scheduler.explain_plan().splitlines() == [
        "Scheduled Give meds (Mochi): HIGH priority, 5 min fits in the time budget.",
        "Skipped Vet visit (Mochi): 120 min did not fit in the remaining time.",
    ]


def test_explain_and_total_before_planning_are_empty():
    """Current behavior: calling these before generate_plan() quietly returns nothing."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, due_date=TODAY))
    scheduler = make_scheduler(pet)

    assert scheduler.explain_plan() == ""
    assert scheduler.get_total_duration() == 0
