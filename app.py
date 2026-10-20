from datetime import datetime, timedelta

import streamlit as st

from pawpal_system import Frequency, Owner, Pet, Priority, Task
from scheduler import Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Colored labels so priority stands out at a glance in tables
PRIORITY_LABEL = {Priority.HIGH: "🔴 HIGH", Priority.MEDIUM: "🟡 MEDIUM", Priority.LOW: "🟢 LOW"}

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
    col1, col2 = st.columns(2, vertical_alignment="bottom")
    with col1:
        frequency = st.selectbox("Repeats", [f.name for f in Frequency])
    with col2:
        has_time = st.checkbox("Fixed start time")
        start_time = st.time_input("Start time", value=None, disabled=not has_time)

    if st.button("Add task"):
        if task_title.strip():
            pet.add_task(
                Task(
                    task_title.strip(),
                    int(duration),
                    Priority[priority],
                    category,
                    time=start_time.strftime("%H:%M") if has_time and start_time else None,
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

    scheduler = Scheduler(owner)

    st.markdown("#### Current tasks")
    st.caption("Sorted by start time; tasks without a fixed time are listed last.")
    col1, col2 = st.columns(2)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All"] + [p.name for p in owner.pets])
    with col2:
        status_filter = st.selectbox("Show status", ["All", "To do", "Done"])
    filtered = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All" else pet_filter,
        completed={"All": None, "To do": False, "Done": True}[status_filter],
    )
    conflicts = scheduler.find_conflicts()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Showing", len(filtered))
    col2.metric("To do", sum(not t.is_completed for _, t in filtered))
    col3.metric("Done", sum(t.is_completed for _, t in filtered))
    col4.metric("Conflicts", len(conflicts))

    rows = [
        {
            "Time": t.time or "Flexible",
            "Pet": p.name,
            "Task": t.title,
            "Minutes": t.duration_minutes,
            "Priority": PRIORITY_LABEL[t.priority],
            "Category": t.category.title(),
            "Repeats": t.frequency.name.title(),
            "Due": t.due_date,
            "Done": t.is_completed,
        }
        for p, t in scheduler.sort_by_time(filtered)
    ]
    if rows:
        st.dataframe(
            rows,
            hide_index=True,
            width="stretch",
            column_config={
                "Minutes": st.column_config.NumberColumn(format="%d min"),
                "Due": st.column_config.DateColumn(format="MMM D, YYYY"),
                "Done": st.column_config.CheckboxColumn(),
            },
        )
    elif scheduler.all_tasks():
        st.info("No tasks match these filters.", icon="🔍")
    else:
        st.info("No tasks yet. Add one above.", icon="📝")

    if conflicts:
        for warning in conflicts:
            st.warning(warning, icon="⚠️")
    elif scheduler.all_tasks():
        st.success("No time conflicts among today's fixed-time tasks.", icon="✅")
else:
    st.caption("Add a pet before adding tasks.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    conflicts = scheduler.find_conflicts()
    if conflicts:
        st.error(
            f"{len(conflicts)} time conflict(s) among today's fixed-time tasks. "
            "Consider moving one task in each pair:",
            icon="🚨",
        )
        for warning in conflicts:
            st.warning(warning, icon="⚠️")

    if not plan and not scheduler.skipped_tasks:
        st.info("There are no unfinished tasks to schedule.", icon="🎉")
    else:
        used = scheduler.get_total_duration()
        budget = owner.available_minutes

        st.markdown(f"#### Today's schedule for {owner.name}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Scheduled", f"{len(plan)} tasks", f"{used} min", delta_color="off")
        col2.metric("Time left", f"{budget - used} min")
        col3.metric("Skipped", len(scheduler.skipped_tasks))
        st.progress(
            min(used / budget, 1.0) if budget else 0.0,
            text=f"{used} of {budget} min used",
        )

        clock = datetime.strptime("08:00", "%H:%M")
        schedule_rows = []
        for p, t in plan:
            end = clock + timedelta(minutes=t.duration_minutes)
            schedule_rows.append(
                {
                    "Slot": f"{clock:%I:%M %p} - {end:%I:%M %p}",
                    "Pet": p.name,
                    "Task": t.title,
                    "Minutes": t.duration_minutes,
                    "Priority": PRIORITY_LABEL[t.priority],
                    "Fixed time": t.time or "Flexible",
                }
            )
            clock = end
        if schedule_rows:
            st.dataframe(
                schedule_rows,
                hide_index=True,
                width="stretch",
                column_config={"Minutes": st.column_config.NumberColumn(format="%d min")},
            )
            st.success(
                f"Planned {len(plan)} task(s) in {used} of {budget} minutes.", icon="✅"
            )

        if scheduler.skipped_tasks:
            st.warning(
                f"{len(scheduler.skipped_tasks)} task(s) didn't fit in the remaining time:",
                icon="⏳",
            )
            st.table(
                [
                    {
                        "Pet": p.name,
                        "Task": t.title,
                        "Minutes": t.duration_minutes,
                        "Priority": PRIORITY_LABEL[t.priority],
                    }
                    for p, t in scheduler.skipped_tasks
                ]
            )

        with st.expander("Why this plan?"):
            for line in scheduler.explain_plan().splitlines():
                st.markdown(f"- {line}")
