# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🧩 Implementation Summary

The code is split into two layers. `pawpal_system.py` holds the core data model (`Priority`, `Task`, `Pet`, `Owner`), and `scheduler.py` holds the planning algorithm (`Scheduler`). Planning ideas for the algorithm are tracked separately in [`algorithm_plan.md`](algorithm_plan.md). The five pieces are:

- **`Priority`**: an enum (`HIGH`, `MEDIUM`, `LOW`) that controls the order tasks are scheduled in. Using an enum instead of a string means a typo raises an error instead of sorting incorrectly.
- **`Task`**: one care activity, with a title, duration, priority, category, and completion status. It checks itself when it is created or updated (a valid priority and a positive duration), and `mark_complete()` marks it as done.
- **`Pet`**: owns a list of tasks. `add_task()` gives each task a unique id, and `remove_task()` / `edit_task()` look tasks up by that id.
- **`Owner`**: holds the daily time budget (`available_minutes`) and the list of pets.
- **`Scheduler`**: takes an `Owner` and plans every pet's tasks against that one shared budget.

**How they work together:** an `Owner` has `Pet`s, and each `Pet` has `Task`s. `Scheduler.generate_plan()` collects every unfinished task from all of the owner's pets, sorts them by priority (shorter tasks first when priorities tie), and adds each task to the plan if it fits in the remaining time. A task that doesn't fit is skipped. Results are stored as `(pet, task)` pairs so the plan shows whose task each one is. `explain_plan()` gives the reason each task was scheduled or skipped, and `get_total_duration()` adds up the scheduled minutes.

`main.py` is a small demo that builds a sample owner, pets, and tasks and prints the plan. The tests in `tests/` cover task completion and adding tasks.

## 🖥️ Sample Output

Running `python main.py` builds a sample owner with two pets and six tasks, then prints the generated plan:

```
==================================================
Today's Schedule for Jordan
Time available: 90 min
==================================================
08:00 AM - 08:05 AM  Luna   Give meds       [HIGH]
08:05 AM - 08:15 AM  Mochi  Breakfast       [HIGH]
08:15 AM - 08:45 AM  Mochi  Morning walk    [HIGH]
08:45 AM - 09:00 AM  Luna   Puzzle feeder   [MEDIUM]
09:00 AM - 09:20 AM  Mochi  Brush coat      [LOW]
--------------------------------------------------
Total scheduled: 80 min

Skipped (not enough time):
  Luna: Laser play (25 min)

Why this plan:
Scheduled Give meds (Luna): HIGH priority, 5 min fits in the time budget.
Scheduled Breakfast (Mochi): HIGH priority, 10 min fits in the time budget.
Scheduled Morning walk (Mochi): HIGH priority, 30 min fits in the time budget.
Scheduled Puzzle feeder (Luna): MEDIUM priority, 15 min fits in the time budget.
Scheduled Brush coat (Mochi): LOW priority, 20 min fits in the time budget.
Skipped Laser play (Luna): 25 min did not fit in the remaining time.
```

Tasks from every pet share the owner's single time budget. They are ordered by priority, with shorter tasks first when priorities tie. Any task that no longer fits in the remaining time is skipped.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

On top of the basic priority-based plan, PawPal+ can sort tasks by clock time, filter them, detect time conflicts, and repeat daily or weekly tasks. The core data lives in `pawpal_system.py`, and the planning logic lives in `scheduler.py` (see [`algorithm_plan.md`](algorithm_plan.md) for design notes). Run `python main.py` to see every feature below in the terminal.

| Feature | Method(s) | Summary |
|---------|-----------|---------|
| Sorting | `Scheduler.sort_by_time()`, `Scheduler.generate_plan()` | Order tasks by their `"HH:MM"` start time, or by priority and then duration for the daily plan. |
| Filtering | `Scheduler.filter_tasks(pet_name, completed)` | Show one pet's tasks, finished or unfinished tasks, or both combined. |
| Conflict detection | `Scheduler.find_conflicts(on)` | Warn when two fixed-time tasks overlap, for the same pet or different pets. |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.complete_task(pet, task_id)` | Completing a daily or weekly task automatically creates the next one. |

### Sorting: `Scheduler.sort_by_time()`

- Each task can have an optional fixed start time, `Task.time`, written as `"HH:MM"`.
- `sort_by_time()` orders `(pet, task)` pairs by that time, using a `lambda`-style key function.
- Times are converted to minutes after midnight before comparing. Plain string sorting would put `"13:15"` before `"9:30"`, because it compares character by character.
- Tasks with no time, or a time that can't be read, go last. Tasks with the same time keep the order they were added.
- It returns a new list, so you can pass in any subset of tasks (for example, the result of `filter_tasks()`).

`Scheduler.generate_plan()` uses a different order for the daily plan: priority first (`HIGH` → `LOW`), then shorter tasks first to break ties.

```
Tasks in the order they were added:      Sorted by time (untimed last):
  --:--  Mochi  Brush coat                  07:00  Mochi  Morning walk
  08:00  Mochi  Breakfast                   08:00  Mochi  Breakfast
  07:00  Mochi  Morning walk                08:00  Luna   Give meds
  19:00  Luna   Laser play                   9:30  Luna   Puzzle feeder
   9:30  Luna   Puzzle feeder               19:00  Luna   Laser play
  08:00  Luna   Give meds                   --:--  Mochi  Brush coat
```

### Filtering: `Scheduler.filter_tasks(pet_name, completed)`

- `pet_name` keeps only tasks for the pet with that exact name.
- `completed=True` keeps finished tasks, and `completed=False` keeps unfinished ones.
- Both filters are optional, and when you give both, a task must match both. Leaving a filter as `None` means "don't filter on this", so `filter_tasks()` with no arguments returns everything.
- An unknown pet name returns an empty list rather than an error.

```python
scheduler.filter_tasks(pet_name="Mochi")                   # all of Mochi's tasks
scheduler.filter_tasks(completed=False)                    # unfinished tasks, every pet
scheduler.filter_tasks(pet_name="Mochi", completed=False)  # Mochi's unfinished tasks
```

`generate_plan()` also filters on its own: it leaves out completed tasks and tasks due after the planning day.

### Conflict detection: `Scheduler.find_conflicts(on)`

- Looks at every unfinished task with a fixed time that's due on the given day (today by default), across **all pets**.
- Turns each task into a start–end range, sorts by start time, and checks every pair with `itertools.combinations`.
- Two tasks conflict when the later one starts **before the earlier one ends**. Overlapping durations count, not just identical start times: a 10-minute task at 08:00 conflicts with one at 08:05. A task that starts exactly when another ends is not a conflict.
- Each warning says whether the clash is for the **same pet** or **different pets**, and whether the tasks start at the same time or just overlap.
- **Lightweight by design:** it returns warning messages and never raises an error or changes the plan. A task with an unreadable time gets its own `Warning:` line, and the other tasks are still checked.

```
Conflict (different pets): Breakfast (Mochi) at 08:00 starts at the same time as Give meds (Luna) at 08:00.
Conflict (same pet): Walk (Mochi) at 08:00 overlaps Breakfast (Mochi) at 08:10.
Warning: couldn't check Give meds (Mochi) for conflicts; time '8am' isn't HH:MM.
```

### Recurring tasks: `Task.next_occurrence()` and `Scheduler.complete_task()`

- Each task has a `frequency` (`ONCE`, `DAILY` or `WEEKLY`) and a `due_date` (today by default).
- `Task.next_occurrence()` holds the rule. It returns an unfinished copy of the task due 1 day later (`DAILY`) or 7 days later (`WEEKLY`), or `None` for `ONCE`. The original task is not changed.
- `Scheduler.complete_task(pet, task_id)` is the one place to finish a task. It marks the task done, then adds the next occurrence to the same pet, which gives it a new id. It raises `KeyError` if the pet has no task with that id.
- Because `generate_plan()` only includes tasks due on or before the planning day, tomorrow's copy doesn't appear in today's plan.
- In the app, the **Mark complete** button calls `complete_task()`.

```
Completed Breakfast (daily; next due 2026-10-20) and Morning walk (one-off).

Filter: Mochi's unfinished tasks:
  --:--  Mochi  Brush coat     [todo] due 2026-10-19
  08:00  Mochi  Breakfast      [todo] due 2026-10-20
```

### Current limitations

- `generate_plan()` still lays tasks out back to back from 8:00 AM and doesn't place fixed-time tasks at their set time.
- Conflicts are reported but not resolved automatically. The owner decides what to move (see section 2b of `reflection.md`).
- The next occurrence is counted from the old due date, so a daily task completed late comes back still overdue.
- The app doesn't have inputs for a task's fixed time yet, so conflict warnings show only in `main.py` and the tests.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
