# 🐾 PawPal+

**PawPal+** is a pet care planning assistant built with Python and Streamlit. You tell it how much time you have today, add your pets and their care tasks, and it builds a daily plan that fits your time budget. It also explains why each task was scheduled or skipped, warns you about clashing appointments, and brings daily and weekly tasks back automatically.

## Contents

- [Features](#-features)
- [Installation](#-installation)
- [Running PawPal+](#-running-pawpal)
- [📸 Demo Walkthrough](#-demo-walkthrough)
- [🧩 How It Works](#-how-it-works)
- [📐 Smarter Scheduling](#-smarter-scheduling)
- [🗂️ Project Structure](#️-project-structure)
- [🧪 Testing PawPal+](#-testing-pawpal)
- [Troubleshooting](#️-troubleshooting)
- [Current limitations](#current-limitations)

## ✨ Features

Each feature links to the code that implements it. Every one is covered by the tests in [`tests/`](tests/).

| Feature | Algorithm | Code |
|---------|-----------|------|
| Greedy daily plan | Sort by priority, then shortest; add each task that fits | [`Scheduler.generate_plan()`](scheduler.py#L154) |
| Sorting by time | Sort on minutes after midnight; untimed tasks last | [`Scheduler.sort_by_time()`](scheduler.py#L53) |
| Filtering | Combine optional pet and status filters with AND | [`Scheduler.filter_tasks()`](scheduler.py#L31) |
| Conflict warnings | Turn tasks into time ranges and check every pair for overlap | [`Scheduler.find_conflicts()`](scheduler.py#L104) |
| Daily and weekly recurrence | Completing a task adds a copy due 1 or 7 days later | [`Task.next_occurrence()`](pawpal_system.py#L56), [`Scheduler.complete_task()`](scheduler.py#L77) |
| Plan explanations | One reason for each scheduled or skipped task | [`Scheduler.explain_plan()`](scheduler.py#L191) |
| Safe task edits | Check changes on a copy before applying any | [`Task.update()`](pawpal_system.py#L69) |

- **Greedy daily plan with a shared time budget.** Every unfinished task due today or earlier, from all pets, is sorted by `(priority, duration)`. `HIGH` goes first, and shorter tasks break ties. The scheduler walks that list once and adds each task that fits in the minutes left, skipping the rest. A shorter task later in the list can still use leftover time, and all pets draw from the owner's one budget, so two pets can't double-book the owner. Overdue tasks are included, while completed and future tasks are not. *Tests:* `test_generate_plan_*` in [`tests/test_scheduler.py`](tests/test_scheduler.py).
- **Sorting by time.** Tasks with a fixed `"HH:MM"` start time are ordered by minutes after midnight, not as text, so `9:30` comes before `13:15`. The sort key is `(has no time, minutes)`, which puts flexible tasks, and any time that can't be read, at the end. Python's sort is stable, so tasks at the same time keep the order they were added. *Test:* `test_sort_by_time_orders_by_clock_and_puts_untimed_last`.
- **Filtering by pet and status.** `filter_tasks(pet_name, completed)` takes two optional filters. `None` means "don't filter on this", and when both are given a task must match both. An unknown pet returns an empty list, not an error. The app's **Show pet** and **Show status** drop-downs call this method. *Test:* `test_filter_tasks_by_pet_and_status`.
- **Conflict warnings.** Each unfinished fixed-time task due that day becomes a `(start, end)` range in minutes. The ranges are sorted by start time and every pair is checked with `itertools.combinations`. Two tasks conflict when the later one starts before the earlier one ends:
  - Overlapping durations are caught, not just identical start times.
  - Back-to-back tasks are not flagged.
  - Each warning says whether the clash is for the same pet or different pets.
  - The check only reports: it never changes the plan or raises an error. A task with an unreadable time gets its own warning, and the other tasks are still checked.

  *Tests:* `test_find_conflicts_*` and `test_bad_time_gives_warning_instead_of_crashing`.
- **Daily and weekly recurrence.** `RECURRENCE_STEP` in [`pawpal_system.py`](pawpal_system.py#L20) maps `DAILY` to 1 day and `WEEKLY` to 7 days. When a task is completed, `next_occurrence()` returns an unfinished copy due that much later, or `None` for `ONCE` tasks. `complete_task()` adds the copy to the same pet, and `Pet.add_task()` gives it a new id. The copy is due in the future, so it stays out of today's plan. *Tests:* `test_completing_daily_task_*`, `test_completing_weekly_task_*`, `test_completing_one_off_task_does_not_recur`.
- **Plan explanations.** After planning, `explain_plan()` gives one plain-language line per task: each scheduled task's priority and length, and for each skipped task, that it didn't fit in the time left. *Test:* `test_explain_plan_mentions_scheduled_and_skipped_tasks`.
- **Input checks and safe edits.** A `Task` checks itself when it's created: priority and frequency must be the right enum, the duration must be positive, and the time must be `HH:MM`. `Task.update()` tries the changes on a copy first, so a bad edit raises an error and leaves the task unchanged. `Pet.add_task()` gives each task a unique id that is never reused. *Tests:* [`tests/test_pawpal.py`](tests/test_pawpal.py).

The [Smarter Scheduling](#-smarter-scheduling) section below covers these algorithms in more depth, with sample output.

## 📦 Installation

**Requirements:** Python 3.10 or newer (the code uses `str | None` type hints) and `pip`.

```bash
git clone <your-repo-url>
cd ai110-module2show-pawpal-starter

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

This installs Streamlit (1.30 or newer) for the app and pytest for the tests.

## 🚀 Running PawPal+

| What | Command | Result |
|------|---------|--------|
| Web app | `streamlit run app.py` | Opens PawPal+ in your browser at `http://localhost:8501` |
| Terminal demo | `python main.py` | Prints a sample plan, sorting, filtering, conflicts and recurrence |
| Tests | `python -m pytest` | Runs the full test suite |

The app keeps your data in the browser session. Refreshing the page starts over with an empty owner.

## 📸 Demo Walkthrough

### Main UI features

Start the app with `streamlit run app.py`. The page has four areas, from top to bottom:

| Area | What you can do |
|------|-----------------|
| **How it works** | Expand a short summary of how plans are built. |
| **Owner** | Set your name and how many minutes you have for pet care today. All pets share this one budget. |
| **Add a Pet** | Add a pet with a name, species (dog, cat, other) and age. |
| **Tasks** | Choose a pet and add a task with a title, duration, priority (`HIGH`/`MEDIUM`/`LOW`), category, how often it repeats (`ONCE`/`DAILY`/`WEEKLY`), and an optional fixed start time. Then:<ul><li>Mark any unfinished task complete.</li><li>Browse the **Current tasks** table, filtered with **Show pet** and **Show status**.</li><li>Read the counters (Showing, To do, Done, Conflicts) and any conflict warnings.</li></ul> |
| **Build Schedule** | Click **Generate schedule** to see:<ul><li>a timetable of today's plan</li><li>counters for tasks scheduled, time left and tasks skipped, and a bar showing budget used</li><li>a table of skipped tasks</li><li>**Why this plan?**, with the reason for each decision</li></ul> |

### Example workflow

This walkthrough uses a 60-minute budget, two pets and four tasks. The results below are what the app produces for these inputs.

1. **Set the owner.** Enter `Jordan` and set **Time available today** to `60`.
2. **Add two pets.** Add `Mochi` (dog, 3), then `Luna` (cat, 5). Both appear under "Your pets".
3. **Add Mochi's tasks.** Choose **Mochi** in the Pet drop-down and add:
   - `Morning walk`: 30 min, HIGH, walk, DAILY, fixed time 08:00
   - `Breakfast`: 10 min, HIGH, feeding, DAILY, fixed time 08:15
   - `Brush coat`: 20 min, LOW, grooming, ONCE, no fixed time
4. **Add Luna's task.** Choose **Luna** and add `Give meds`: 5 min, HIGH, meds, ONCE, fixed time 09:00.
5. **Review the task list.** The **Current tasks** table is sorted by start time, not by the order you entered tasks: Morning walk (08:00), Breakfast (08:15), Give meds (09:00), then Brush coat (Flexible). Set **Show pet** to `Luna` to see only Give meds, then set it back to `All`.
6. **See the conflict warning.** The walk runs 08:00–08:30, so it overlaps breakfast at 08:15. The Conflicts counter shows `1`, and a warning appears under the table:
   > ⚠️ Conflict (same pet): Morning walk (Mochi) at 08:00 overlaps Breakfast (Mochi) at 08:15.
7. **Generate today's schedule.** Click **Generate schedule**. The conflict is repeated in red at the top, then the plan shows:

   | Slot | Pet | Task | Priority |
   |------|-----|------|----------|
   | 08:00 AM - 08:05 AM | Luna | Give meds | 🔴 HIGH |
   | 08:05 AM - 08:15 AM | Mochi | Breakfast | 🔴 HIGH |
   | 08:15 AM - 08:45 AM | Mochi | Morning walk | 🔴 HIGH |

   The summary reads **Planned 3 task(s) in 45 of 60 minutes**. **Brush coat** (LOW, 20 min) is listed as skipped, because only 15 minutes were left.
8. **Read the reasons.** Open **Why this plan?**:
   ```
   Scheduled Give meds (Luna): HIGH priority, 5 min fits in the time budget.
   Scheduled Breakfast (Mochi): HIGH priority, 10 min fits in the time budget.
   Scheduled Morning walk (Mochi): HIGH priority, 30 min fits in the time budget.
   Skipped Brush coat (Mochi): 20 min did not fit in the remaining time.
   ```
9. **Complete a recurring task.** Under **Tasks**, choose Mochi, pick **Breakfast**, and click **Mark complete**. The app confirms *"Done! Breakfast repeats daily; next due …"* with tomorrow's date. A new unfinished Breakfast now appears in the table, due tomorrow. Set **Show status** to `Done` to see the finished one.

### Scheduler behaviors shown

| Behavior | Where you see it in the walkthrough | Method |
|----------|-------------------------------------|--------|
| Sorting by time | Step 5: the table is in clock order, with the flexible task last | `Scheduler.sort_by_time()` |
| Filtering | Steps 5 and 9: **Show pet** and **Show status** | `Scheduler.filter_tasks()` |
| Conflict warnings | Step 6: an overlap, not just a matching start time, is caught | `Scheduler.find_conflicts()` |
| Priority-first greedy plan | Step 7: all HIGH tasks first, shortest first; one budget for both pets | `Scheduler.generate_plan()` |
| Skipping what doesn't fit | Step 7: Brush coat is skipped | `Scheduler.generate_plan()` |
| Explanations | Step 8 | `Scheduler.explain_plan()` |
| Daily recurrence | Step 9: tomorrow's Breakfast is added automatically | `Scheduler.complete_task()`, `Task.next_occurrence()` |

Step 7 also shows a [current limitation](#current-limitations): the timetable lays tasks out back to back from 8:00 AM, so Breakfast is placed at 08:05 even though its fixed time is 08:15.

### Sample CLI output (`python main.py`)

The terminal demo builds a sample owner (90 minutes, two pets, six tasks) and prints each feature in turn: the daily plan, sorting, filtering, conflicts, and recurrence. Dates show the day you run it.

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

==================================================
Sorting and filtering
==================================================

Tasks in the order they were added:
  --:--  Mochi  Brush coat     [todo] due 2026-10-19
  08:00  Mochi  Breakfast      [todo] due 2026-10-19
  07:00  Mochi  Morning walk   [todo] due 2026-10-19
  19:00  Luna   Laser play     [todo] due 2026-10-19
   9:30  Luna   Puzzle feeder  [todo] due 2026-10-19
  08:00  Luna   Give meds      [todo] due 2026-10-19

Sorted by time (untimed last):
  07:00  Mochi  Morning walk   [todo] due 2026-10-19
  08:00  Mochi  Breakfast      [todo] due 2026-10-19
  08:00  Luna   Give meds      [todo] due 2026-10-19
   9:30  Luna   Puzzle feeder  [todo] due 2026-10-19
  19:00  Luna   Laser play     [todo] due 2026-10-19
  --:--  Mochi  Brush coat     [todo] due 2026-10-19

Filter: Luna's tasks, sorted by time:
  08:00  Luna   Give meds      [todo] due 2026-10-19
   9:30  Luna   Puzzle feeder  [todo] due 2026-10-19
  19:00  Luna   Laser play     [todo] due 2026-10-19

Conflicts:
  Conflict (different pets): Breakfast (Mochi) at 08:00 starts at the same time as Give meds (Luna) at 08:00.

Completed Breakfast (daily; next due 2026-10-20) and Morning walk (one-off).

Filter: completed tasks:
  08:00  Mochi  Breakfast      [done] due 2026-10-19
  07:00  Mochi  Morning walk   [done] due 2026-10-19

Filter: Mochi's unfinished tasks:
  --:--  Mochi  Brush coat     [todo] due 2026-10-19
  08:00  Mochi  Breakfast      [todo] due 2026-10-20

Filter: unknown pet 'Rex':
  (none)
```

## 🧩 How It Works

The code is split into two layers. `pawpal_system.py` holds the core data model (`Priority`, `Frequency`, `Task`, `Pet`, `Owner`), and `scheduler.py` holds the planning logic (`Scheduler`). `app.py` is the Streamlit interface and only calls these classes; it holds no scheduling logic of its own. Planning ideas for the algorithm are tracked in [`algorithm_plan.md`](algorithm_plan.md).

- **`Priority`**: an enum (`HIGH`, `MEDIUM`, `LOW`) that controls the order tasks are scheduled in. Using an enum instead of a string means a typo raises an error instead of sorting incorrectly.
- **`Frequency`**: an enum (`ONCE`, `DAILY`, `WEEKLY`) that decides whether a task comes back after it's completed.
- **`Task`**: one care activity, with a title, duration, priority, category, completion status, optional fixed time, frequency and due date. It checks itself when it is created or updated (a valid priority and frequency, a positive duration, and an `HH:MM` time).
- **`Pet`**: owns a list of tasks. `add_task()` gives each task a unique id, and `remove_task()` / `edit_task()` look tasks up by that id.
- **`Owner`**: holds the daily time budget (`available_minutes`) and the list of pets.
- **`Scheduler`**: takes an `Owner` and plans every pet's tasks against that one shared budget.

**How they work together:** an `Owner` has `Pet`s, and each `Pet` has `Task`s. `Scheduler.generate_plan()` collects every unfinished task due today or earlier from all of the owner's pets, sorts them by priority (shorter tasks first when priorities tie), and adds each task to the plan if it fits in the remaining time. A task that doesn't fit is skipped. Results are stored as `(pet, task)` pairs so the plan shows whose task each one is. `explain_plan()` gives the reason each task was scheduled or skipped, and `get_total_duration()` adds up the scheduled minutes.

For a full run of the terminal demo, see the [sample CLI output](#sample-cli-output-python-mainpy) in the walkthrough.

## 📐 Smarter Scheduling

On top of the basic priority-based plan, PawPal+ can sort tasks by clock time, filter them, detect time conflicts, and repeat daily or weekly tasks. Run `python main.py` to see every feature below in the terminal, or use them in the app as described in the [walkthrough](#-demo-walkthrough).

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
- In the app, the **Current tasks** table is always shown in this order.

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
- In the app, the **Show pet** and **Show status** drop-downs call this method.

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
- In the app, each warning is shown under the task table and again above the generated schedule.

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

## 🗂️ Project Structure

```
.
├── app.py                 # Streamlit web app (UI only; calls the classes below)
├── pawpal_system.py       # Data model: Priority, Frequency, Task, Pet, Owner
├── scheduler.py           # Planning logic: Scheduler
├── main.py                # Terminal demo of every feature
├── tests/
│   ├── test_pawpal.py     # Data model tests
│   ├── test_scheduler.py  # Scheduling tests
│   └── test_app.py        # Streamlit app and main.py tests
├── diagrams/
│   ├── uml_final.mmd                # Final UML class diagram (Mermaid)
│   └── complete_task_sequence.mmd   # Sequence diagram for completing a task
├── algorithm_plan.md      # Design notes for the scheduling algorithms
├── reflection.md          # Design decisions and project reflection
└── requirements.txt
```

### UML diagrams

The diagrams are written in [Mermaid](https://mermaid.js.org/). To view them, paste a `.mmd` file into [mermaid.live](https://mermaid.live), or open it in an editor with a Mermaid preview (Mermaid 10.3 or newer).

- [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) shows every class, its fields and methods, and how the classes relate. Classes are grouped by the file they live in.
- [`diagrams/complete_task_sequence.mmd`](diagrams/complete_task_sequence.mmd) shows the calls between `Scheduler`, `Pet` and `Task` when a task is completed and comes back.

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

The tests live in `tests/`. `test_pawpal.py` covers the data model in `pawpal_system.py`, `test_scheduler.py` covers the planning logic in `scheduler.py`, and `test_app.py` covers the Streamlit app and the `main.py` demo:

- **Tasks and pets:** creating a valid task fills in defaults, and an invalid priority, duration, frequency or time is rejected. Task ids are unique and never reused. Adding, editing and removing a task changes only that task, and a rejected edit leaves the task exactly as it was.
- **Sorting:** `sort_by_time()` returns tasks in chronological order, compared as clock times (so `9:30` comes before `13:15`), with untimed tasks last.
- **Filtering:** `filter_tasks()` narrows by pet, by completion status, or both.
- **Recurrence:** marking a daily task complete adds a new, unfinished task due the next day, and a weekly task comes back 7 days later. One-off tasks don't come back, and tomorrow's copy isn't planned today.
- **Conflict detection:** two tasks at the same start time are flagged for the same pet and across pets. Overlapping durations are flagged too, but back-to-back tasks, completed tasks and tasks on other days are not. A bad time gives a warning instead of crashing.
- **Daily plan:** `generate_plan()` orders tasks by priority and then by shortest task, skips tasks that don't fit, uses leftover time for shorter tasks, and shares one budget across all pets. `explain_plan()` and `get_total_duration()` report the result.
- **App:** using Streamlit's `AppTest` (no browser needed), the tests add pets and tasks through the forms, reject blank names, click **Mark complete** on a daily task, and generate a schedule that shows the plan summary and a table of skipped tasks. `main.py` is run from start to finish.

Sample test output (`python -m pytest`):

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\heinh\ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collected 55 items

tests\test_app.py ........                                               [ 14%]
tests\test_pawpal.py .......................                             [ 56%]
tests\test_scheduler.py ........................                         [100%]

============================= 55 passed in 2.57s ==============================
```

**Confidence Level: ★★★★★ (5/5)**

- All 55 tests pass, with no known bugs and no expected failures.
- Every layer is tested: the data model, every scheduling feature (sorting, filtering, recurrence, conflict detection and the daily plan), and the app's main actions from the user's side.
- The tests include edge cases, such as a task that exactly fills the time budget, back-to-back tasks that shouldn't conflict, overdue tasks, a rejected edit, and a bad time that shouldn't crash the app.
- This rating is about how reliably the built features work. Some features are still simpler than planned (see [Current limitations](#current-limitations)). For example, the plan doesn't place fixed-time tasks at their set time.

## 🛠️ Troubleshooting

- **`python -m pytest` fails in PowerShell but works in Bash.** A Windows "app execution alias" `python.exe` may come before your real Python on the PATH. Turn it off in *Settings → Apps → Advanced app settings → App execution aliases*, or activate the virtual environment first.
- **`streamlit: command not found`.** Activate the virtual environment and run `pip install -r requirements.txt` again, or use `python -m streamlit run app.py`.
- **My pets and tasks disappeared.** Data lives only in the current browser session, so refreshing the page or restarting the app clears it.
- **A fixed-time task is placed at a different time in the schedule.** This is a known limitation; see below.

## Current limitations

- `generate_plan()` still lays tasks out back to back from 8:00 AM and doesn't place fixed-time tasks at their set time.
- Conflicts are reported but not resolved automatically. The owner decides what to move (see section 2b of `reflection.md`).
- The next occurrence is counted from the old due date, so a daily task completed late comes back still overdue.
- Data isn't saved between sessions.
- The app can add and complete tasks, but not edit or remove them yet. `Pet.edit_task()` and `Pet.remove_task()` exist in the code but have no buttons.
