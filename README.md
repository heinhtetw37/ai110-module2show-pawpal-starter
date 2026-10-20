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

The scheduling logic lives in `pawpal_system.py` and is built from five pieces:

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

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
