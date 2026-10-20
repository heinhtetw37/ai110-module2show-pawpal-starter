from datetime import datetime, timedelta

import streamlit as st

from pawpal_system import Frequency, Owner, Pet, Priority, Task
from scheduler import Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
**PawPal+** is a pet care planning assistant. Tell it how much time you have today,
add your pets and their care tasks, and it builds a daily plan that fits your schedule.
"""
)

with st.expander("How it works", expanded=False):
    st.markdown(
        """
1. **Set your time budget**: enter how many minutes you have for pet care today.
2. **Add your pets**: each pet keeps its own list of care tasks.
3. **Add tasks**: give each task a duration, a priority (HIGH, MEDIUM, LOW), and a category.
4. **Generate a schedule**: tasks from all your pets share one time budget. Higher-priority
   tasks are scheduled first (shorter tasks first when priorities tie), and any task that
   doesn't fit in the remaining time is skipped.
5. **Read the explanation**: the plan shows why each task was scheduled or skipped.
"""
    )

st.divider()

# Create the Owner once; session_state keeps the same object across reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)
owner = st.session_state.owner

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input(
            "Time available today (minutes)",
            min_value=0,
            max_value=1440,
            value=owner.available_minutes,
        )
    )

st.subheader("Add a Pet")
col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    age = st.number_input("Age", min_value=0, max_value=40, value=0)

if st.button("Add pet"):
    if pet_name.strip():
        owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age)))
    else:
        st.error("Pet name can't be empty.")

if owner.pets:
    st.write("Your pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")

if owner.pets:
    pet_index = st.selectbox(
        "Pet",
        range(len(owner.pets)),
        format_func=lambda i: owner.pets[i].name,
    )
    pet = owner.pets[pet_index]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", [p.name for p in Priority], index=0)
    with col4:
        category = st.selectbox(
            "Category", ["walk", "feeding", "meds", "enrichment", "grooming", "general"]
        )
    frequency = st.selectbox("Repeats", [f.name for f in Frequency])

    if st.button("Add task"):
        if task_title.strip():
            pet.add_task(
                Task(
                    task_title.strip(),
                    int(duration),
                    Priority[priority],
                    category,
                    frequency=Frequency[frequency],
                )
            )
        else:
            st.error("Task title can't be empty.")

    unfinished = [t for t in pet.tasks if not t.is_completed]
    if unfinished:
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        with col1:
            done_id = st.selectbox(
                f"Mark one of {pet.name}'s tasks complete",
                [t.id for t in unfinished],
                format_func=lambda i: next(
                    f"{t.title} (due {t.due_date})" for t in unfinished if t.id == i
                ),
            )
        with col2:
            if st.button("Mark complete"):
                next_task = Scheduler(owner).complete_task(pet, done_id)
                if next_task:
                    st.success(
                        f"Done! {next_task.title} repeats "
                        f"{next_task.frequency.name.lower()}; next due {next_task.due_date}."
                    )
                else:
                    st.success("Done!")

    rows = [
        {
            "Pet": p.name,
            "Task": t.title,
            "Minutes": t.duration_minutes,
            "Priority": t.priority.name,
            "Category": t.category,
            "Repeats": t.frequency.name,
            "Due": str(t.due_date),
            "Status": "done" if t.is_completed else "todo",
        }
        for p in owner.pets
        for t in p.tasks
    ]
    if rows:
        st.write("Current tasks:")
        st.table(rows)
    else:
        st.info("No tasks yet. Add one above.")
else:
    st.caption("Add a pet before adding tasks.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    if not plan and not scheduler.skipped_tasks:
        st.info("There are no unfinished tasks to schedule.")
    else:
        st.markdown(f"**Today's schedule for {owner.name}**")
        clock = datetime.strptime("08:00", "%H:%M")
        schedule_rows = []
        for p, t in plan:
            end = clock + timedelta(minutes=t.duration_minutes)
            schedule_rows.append(
                {
                    "Time": f"{clock:%I:%M %p} - {end:%I:%M %p}",
                    "Pet": p.name,
                    "Task": t.title,
                    "Priority": t.priority.name,
                }
            )
            clock = end
        if schedule_rows:
            st.table(schedule_rows)
        st.success(
            f"Total scheduled: {scheduler.get_total_duration()} of "
            f"{owner.available_minutes} min"
        )

        if scheduler.skipped_tasks:
            st.warning(
                "Skipped (not enough time): "
                + ", ".join(
                    f"{p.name}: {t.title} ({t.duration_minutes} min)"
                    for p, t in scheduler.skipped_tasks
                )
            )

        with st.expander("Why this plan?", expanded=True):
            st.text(scheduler.explain_plan())
