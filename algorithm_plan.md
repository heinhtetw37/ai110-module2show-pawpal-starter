# PawPal+ Algorithm Plan

This file is for planning the scheduling algorithm. The code it describes lives in `scheduler.py`. The core data model (`Priority`, `Task`, `Pet`, `Owner`) lives in `pawpal_system.py` and should only change when a feature needs a new field.

## Current algorithm

`Scheduler.generate_plan()` is a greedy planner:

1. Collect every unfinished task from all of the owner's pets.
2. Sort by priority (HIGH first), then by duration (shorter first) to break ties.
3. Go through the sorted list and schedule each task that fits in the remaining minutes. Skip the ones that don't.

**Limitations found when reviewing `main.py`:**

- Start and end times are calculated in `main.py` and `app.py`, not in the scheduler, and the same loop is copied in both.
- A HIGH task that doesn't fit is skipped the same way a LOW one is, even if it's meds.
- There's no time of day: tasks run back to back from 8:00 AM.
- Tasks are one-offs, so nothing recurs daily or weekly.
- `category` is stored but never used.
- Explanations are generic, and completed tasks disappear without being mentioned.
- `explain_plan()` and `get_total_duration()` quietly return empty or 0 if called before `generate_plan()`.

## Planned features

Listed in the order I plan to build them. Each one has a test idea so the change can be checked.

### 1. Time slots in the scheduler

- **Change:** `generate_plan(start="08:00")` gives each scheduled task a start and end time. `main.py` and `app.py` read those times instead of calculating their own.
- **Test:** three tasks of 10, 20 and 30 min starting at 08:00 should end at 08:10, 08:30 and 09:00.

### 2. Required tasks

- **Change:** add `Task.required: bool = False`. Required tasks are scheduled before anything else, whatever their priority. If required tasks alone go over the budget, the plan warns clearly instead of quietly skipping one.
- **Test:** a required 60-min task with a 50-min budget should produce a warning and must not be silently skipped.

### 3. Clearer explanations

- **Change:** say why each task came in its position (for example, "HIGH priority, shortest of 3 HIGH tasks"). Show how many minutes were left when a task was skipped, and list completed tasks as "already done".
- **Test:** a skipped task's explanation should include the minutes that were left (for example, "needed 25 min, 10 left").

### 4. Preferred time of day (conflict handling)

> **Partly done:** `Task.time` (a fixed `"HH:MM"` start), `Scheduler.sort_by_time()` and `Scheduler.find_conflicts()` are built and tested. Still to do: `generate_plan()` placing fixed-time tasks at their set time.

- **Change:** add an optional `Task.preferred_time` (morning, afternoon or evening, or a fixed clock time). Place fixed-time tasks first, then fill the gaps. Two fixed tasks that overlap should be reported as a conflict.
- **Test:** two tasks both fixed at 08:00 should report a conflict, and a task fixed at 18:00 should never be placed in the morning.

### 5. Recurring tasks

> **Done:** `Task.frequency`, `Task.due_date`, `Task.next_occurrence()` (the recurrence rule) and `Scheduler.complete_task()` (marks the task done and adds the next copy to the pet), tested in `tests/`. The app has a "Mark complete" button that uses it. Note: the next due date is counted from the old due date, so an overdue daily task comes back still overdue.

- **Change:** add `Task.frequency` (once, daily or weekly). When a daily task is marked complete, it comes back the next day instead of disappearing.
- **Test:** completing a daily task and then planning for the next day should include it again. A one-off task should not come back.

## Conflict detection strategy (lightweight)

`Scheduler.find_conflicts(on)` is deliberately lightweight: it **reports** problems as messages and never raises an error or changes the plan.

- **What it checks:** unfinished tasks with a fixed time that are due on the given day, across all pets. Each warning says whether the clash is for the same pet or for different pets, and whether the tasks start at the same time or just overlap.
- **How:** sort the tasks by start time, then check every pair with `itertools.combinations`. Two tasks conflict if the later one starts before the earlier one ends.
- **Tradeoff:** an earlier version stopped comparing as soon as the next task started after the current one ended. That was about 3× faster on 500 tasks (2.3 ms vs 7.0 ms), but harder to read. A pet owner has around 10–20 timed tasks a day, so I chose the simpler version.
- **Bad data:** a time that can't be read (for example, `"8am"` set directly on a task, which skips validation) adds a `Warning:` message for that task, and the other tasks are still checked. `sort_by_time()` puts such tasks last, alongside untimed tasks, instead of crashing.
- **What it doesn't do:** it doesn't fix conflicts (for example, by moving a task), and it doesn't stop you adding a task that clashes. The owner decides.
- **Why:** one bad task shouldn't crash the app or hide other warnings, and a warning lets the owner decide. For example, two pets' breakfasts at 08:00 might be fine if they can be done together.

## Open questions

- Should a required task that can't fit push out a lower-priority task that is already scheduled, or only produce a warning?
- Should the greedy approach stay, or should the planner aim to use as many of the available minutes as possible? For example, two 15-min tasks could fill 30 minutes better than one 20-min task. Greedy is simpler to explain, which matters for `explain_plan()`.
- Should `category` affect planning (for example, no two walks back to back), or only be used for display?

## Design rules

- Planning logic goes in `scheduler.py`. `pawpal_system.py` gets new fields such as `required`, `preferred_time` and `frequency`, plus rules about a single task on its own (like `Task.next_occurrence()`), but never rules that compare or arrange several tasks.
- Every new feature gets a test in `tests/` before it's shown in `app.py`.
