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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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
