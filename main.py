"""Temporary terminal testing ground for PawPal+ logic."""

from datetime import datetime, timedelta

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def main() -> None:
    """Build a sample owner with pets and print today's schedule."""
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", 30, Priority.HIGH, "walk"))
    mochi.add_task(Task("Breakfast", 10, Priority.HIGH, "feeding"))
    mochi.add_task(Task("Brush coat", 20, Priority.LOW, "grooming"))
    luna.add_task(Task("Give meds", 5, Priority.HIGH, "meds"))
    luna.add_task(Task("Puzzle feeder", 15, Priority.MEDIUM, "enrichment"))
    luna.add_task(Task("Laser play", 25, Priority.LOW, "enrichment"))

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


if __name__ == "__main__":
    main()
