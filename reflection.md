# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

The initial design is built around three core actions a user needs to perform:

1. **Enter owner and pet information.** The user starts by telling the app who they are and which pet they are caring for (for example, the owner's name, the pet's name and species, and how much time the owner has available each day). This gives the scheduler the basic context and the time constraint it must plan around.

2. **Add and edit care tasks.** The user can create tasks such as walks, feeding, medication, enrichment, or grooming. Each task has at minimum a title, a duration, and a priority, and the user can change or remove a task later as the pet's needs change.

3. **Generate and view a daily plan.** The user asks the app to build a schedule for the day. The app selects and orders tasks based on priority and the owner's available time, then displays the plan along with a short explanation of why each task was included, ordered where it was, or left out.

From those actions, I identified four main objects:

| Object | Attributes (what it holds) | Methods (what it does) |
|--------|----------------------------|------------------------|
| **Owner** | `name`, `available_minutes` (daily time budget), `pets` | `add_pet(pet)` |
| **Pet** | `name`, `species`, `age`, `tasks` | `add_task(task)`, `remove_task(task_id)`, `edit_task(task_id, **changes)` |
| **Task** | `id`, `title`, `category` (walk, feeding, meds, enrichment, grooming), `duration_minutes`, `priority` (high/medium/low), `is_completed` | `mark_complete()`, `update(**changes)` |
| **Scheduler** | `owner`, `pet`, `scheduled_tasks`, `skipped_tasks` | `generate_plan()` (sort by priority, fit within the time budget), `explain_plan()` (reason for each included/skipped task), `get_total_duration()` |

Relationships: an Owner has zero or more Pets, a Pet has many Tasks, and the Scheduler reads from an Owner and Pet to produce the plan.

My initial UML design uses four classes. Three of them hold data, and one holds the planning logic:

- **Task** is the smallest unit of care: one thing that needs to happen, such as a walk or a feeding. It is responsible for knowing how long it takes, how important it is, and whether it has been done. It can mark itself complete and update its own fields. I made it a dataclass because it is mostly data.
- **Pet** represents the animal being cared for and owns its list of tasks. It is responsible for managing that list: adding, removing, and editing tasks. Keeping tasks on the pet means each pet's care needs stay grouped together.
- **Owner** represents the user. It holds the most important constraint, `available_minutes`, which is how much time the owner has for pet care today, and keeps track of their pets.
- **Scheduler** is the "brain" of the system. It takes an Owner and a Pet, decides which tasks fit into the available time (highest priority first), records what was scheduled and what was skipped, and explains its choices. I kept it as a separate regular class, not a dataclass, so that the scheduling rules live in one place instead of being spread across the data classes. This also makes the logic easier to test and change later.

I kept the design small on purpose. I left out features such as owner preferences and specific time slots until the basic plan works.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes. My first draft had more methods and attributes than the system needed, so I simplified it before writing any logic:

- **Removed `Owner.preferences`**: nothing in the scheduler used it yet, so it only added complexity.
- **Removed `Owner.get_all_tasks()` and `Owner.update_availability()`**: the scheduler plans one pet at a time, so collecting every pet's tasks wasn't needed, and updating availability was just setting one attribute, which can be done directly.
- **Removed `Pet.get_tasks()`**: it only returned the `tasks` list, which is already public.
- **Removed `Task.__str__()`** from the diagram because I never implemented it.
- **Changed the Owner → Pet relationship from "1..\*" to "0..\*"**: an owner can exist before adding a pet, so requiring at least one pet didn't match how the app is used.

I then turned the UML into a class skeleton in `pawpal_system.py`. `Task`, `Pet`, and `Owner` are dataclasses because they mainly hold data. `Scheduler` is a regular class because it holds the planning behavior.

When I reviewed the skeleton, I found three structural problems and changed the design to fix them:

- **The Scheduler now takes only the Owner.** It used to take one Owner and one Pet, but it used the owner's whole time budget for that one pet. Planning two pets separately would have double-booked the owner's time. Now it plans across all of `owner.pets` with one shared budget. It stores results as `(pet, task)` pairs so the plan still shows whose task each one is. This also removed the risk of passing in a pet that doesn't belong to the owner.
- **`priority` is now a `Priority` enum (HIGH/MEDIUM/LOW)** instead of a free-text string. Before, a typo like `"High"` would have sorted incorrectly without any error. `Task.__post_init__` now rejects invalid priorities and non-positive durations.
- **Task ids are now assigned by `Pet.add_task`** using a per-pet counter (`_next_id`), instead of the caller choosing them. This prevents duplicate ids that could make `remove_task` or `edit_task` act on the wrong task.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**My scheduler detects time conflicts but does not resolve them.** `Scheduler.find_conflicts()` checks every pair of unfinished fixed-time tasks due that day, across all pets. It compares full durations, not just start times, so a 10-minute breakfast at 08:00 conflicts with meds at 08:05 even though their start times differ. When it finds an overlap, it returns a warning message such as:

```
Conflict (different pets): Breakfast (Mochi) at 08:00 starts at the same time as Give meds (Luna) at 08:00.
```

That is all it does. It doesn't move either task to a free slot, doesn't refuse to add a task that clashes, and never raises an error. Even a task with an unreadable time just produces a `Warning:` line, and the other tasks are still checked.

The cost is that the owner has to fix conflicts themselves, and a busy owner could miss a warning. A smarter scheduler could automatically push the lower-priority task to the next open time.

I think this tradeoff is reasonable for PawPal+ for three reasons:

- **Not every conflict is a real problem.** Feeding two pets at 08:00 may be fine if they eat side by side, but giving meds while walking the dog is not. The scheduler can't tell these apart, and the owner can.
- **Automatic rescheduling could do harm quietly.** Moving a medication to a later time without asking could matter more than a missed walk. A warning keeps the owner in control of time-sensitive care.
- **It keeps the app reliable and the code simple.** Because it only reports, one bad task can't crash the app or hide other warnings. The check itself is a short loop over every pair of tasks, which is easy to read and test, and fast enough for the 10–20 timed tasks a pet owner has in a day.

If I added automatic rescheduling later, I'd make it a suggestion the owner can accept or reject ("Move Give meds to 08:10?") rather than a silent change.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used Claude Code (an AI coding assistant) at almost every stage of the project:

- **Design:** turning my UML diagram into class skeletons in `pawpal_system.py`, and reviewing that skeleton for structural problems before I wrote any scheduling logic.
- **Refactoring:** the AI pointed out that a Scheduler built for one Owner and one Pet would give the owner's full time budget to each pet, so planning two pets would double-book the owner. It suggested planning across all of the owner's pets with one shared budget. It also suggested replacing the free-text priority with a `Priority` enum and having `Pet.add_task` assign task ids automatically.
- **Testing:** drafting the first two tests, one for `mark_complete()` and one for `add_task()`.
- **Debugging:** working out why `python -m pytest` failed in my PowerShell terminal but worked in Bash. The cause was that a Windows "app execution alias" `python.exe` came before my real Python on the PATH.
- **Documentation:** adding docstrings and writing the implementation summary in the README.

The most helpful prompts were short, specific requests with a clear success condition, such as "Verify that calling `mark_complete()` actually changes the task's status." Asking the AI to *review* code I already had ("what is structurally wrong with this skeleton?") was more useful than asking it to write new code, because it found design bugs I hadn't noticed.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

I did not accept the first class design as-is. The first draft included `Owner.preferences`, `Owner.get_all_tasks()`, `Owner.update_availability()`, `Pet.get_tasks()`, and `Task.__str__()`. I removed all of them because nothing in the scheduler used them yet, or because they only wrapped an attribute that was already public. I also changed the Owner → Pet relationship from "1..\*" to "0..\*", since an owner can exist before they add a pet. Keeping the design small made the later refactor easier to reason about.

I also chose which suggestions to act on. When debugging the PowerShell problem, the AI offered a quick workaround (`py -m pytest`) and two permanent fixes (turning off the alias, or reordering PATH). When I asked for docstrings, it reported that every method already had one, and offered to add class docstrings instead. I didn't take that offer because the methods were what I needed documented.

I verified the AI's work in three ways:

1. **Running the tests.** After each change, I ran `python -m pytest` and checked that both tests still passed. The tests check the value *before* and *after* the action (for example, that `is_completed` starts as `False` and becomes `True`). That way a test can't pass just because the field already had the right value from the start.
2. **Running the demo and checking it by hand.** I ran `python main.py` and checked the printed plan against the rules: HIGH-priority tasks come first, shorter tasks come first when priorities tie, the total (80 min) stays within the 90-minute budget, and "Laser play" (25 min) is correctly skipped because only 10 minutes are left.
3. **Reviewing the diff.** Before committing, I read through the changes with `git diff` to make sure the AI only edited what I asked for.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
