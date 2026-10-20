"""Temporary terminal testing ground for PawPal+ logic."""

from datetime import datetime, timedelta

from pawpal_system import Frequency, Owner, Pet, Priority, Task
from scheduler import Scheduler


def print_tasks(heading: str, pairs: list[tuple[Pet, Task]]) -> None:
    """Print a heading and one line per (pet, task) pair."""
    print(f"\n{heading}:")
    if not pairs:
        print("  (none)")
    for pet, task in pairs:
        status = "done" if task.is_completed else "todo"
        print(
            f"  {task.time or '--:--':>5}  {pet.name:<6} {task.title:<14} "
            f"[{status}] due {task.due_date}"
        )


def main() -> None:
    """Build a sample owner with pets and print today's schedule."""
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks are added out of time order on purpose, to exercise sort_by_time()
    breakfast = Task(
        "Breakfast", 10, Priority.HIGH, "feeding", time="08:00", frequency=Frequency.DAILY
    )
    walk = Task("Morning walk", 30, Priority.HIGH, "walk", time="07:00")
    mochi.add_task(Task("Brush coat", 20, Priority.LOW, "grooming"))  # no fixed time
    mochi.add_task(breakfast)
    mochi.add_task(walk)
    luna.add_task(Task("Laser play", 25, Priority.LOW, "enrichment", time="19:00"))
    # "9:30" has no leading zero; it should still sort before "19:00"
    luna.add_task(Task("Puzzle feeder", 15, Priority.MEDIUM, "enrichment", time="9:30"))
    # Same time as Mochi's 08:00 breakfast, so find_conflicts() should flag it
    luna.add_task(
        Task("Give meds", 5, Priority.HIGH, "meds", time="08:00", frequency=Frequency.DAILY)
    )

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    print("=" * 50)
    print(f"Today's Schedule for {owner.name}")
    print(f"Time available: {owner.available_minutes} min")
    print("=" * 50)

    clock = datetime.strptime("08:00", "%H:%M")
    for pet, task in plan:
        end = clock + timedelta(minutes=task.duration_minutes)
        print(
            f"{clock:%I:%M %p} - {end:%I:%M %p}  "
            f"{pet.name:<6} {task.title:<15} [{task.priority.name}]"
        )
        clock = end

    print("-" * 50)
    print(f"Total scheduled: {scheduler.get_total_duration()} min")

    if scheduler.skipped_tasks:
        print("\nSkipped (not enough time):")
        for pet, task in scheduler.skipped_tasks:
            print(f"  {pet.name}: {task.title} ({task.duration_minutes} min)")

    print("\nWhy this plan:")
    print(scheduler.explain_plan())

    print("\n" + "=" * 50)
    print("Sorting and filtering")
    print("=" * 50)

    print_tasks("Tasks in the order they were added", scheduler.all_tasks())
    print_tasks("Sorted by time (untimed last)", scheduler.sort_by_time())
    print_tasks("Filter: Luna's tasks, sorted by time", scheduler.sort_by_time(
        scheduler.filter_tasks(pet_name="Luna")
    ))

    print("\nConflicts:")
    for warning in scheduler.find_conflicts() or ["None"]:
        print(f"  {warning}")

    # Complete one recurring task and one one-off task, then filter by status
    next_breakfast = scheduler.complete_task(mochi, breakfast.id)
    scheduler.complete_task(mochi, walk.id)
    print(f"\nCompleted {breakfast.title} (daily; next due {next_breakfast.due_date}) "
          f"and {walk.title} (one-off).")

    print_tasks("Filter: completed tasks", scheduler.filter_tasks(completed=True))
    print_tasks("Filter: Mochi's unfinished tasks", scheduler.filter_tasks(
        pet_name="Mochi", completed=False
    ))
    print_tasks("Filter: unknown pet 'Rex'", scheduler.filter_tasks(pet_name="Rex"))


if __name__ == "__main__":
    main()
