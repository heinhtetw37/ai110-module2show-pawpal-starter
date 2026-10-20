"""Tests for the Streamlit app (app.py) and the terminal demo (main.py).

The app tests use Streamlit's AppTest, which runs app.py without a browser and
lets a test fill in widgets and click buttons.
"""

import runpy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from pawpal_system import Frequency

ROOT = Path(__file__).resolve().parent.parent


def widget(widgets, label):
    """Return the widget in a list (such as at.text_input) with the given label."""
    return next(w for w in widgets if w.label == label)


@pytest.fixture
def app():
    """A freshly loaded app with no pets."""
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
    at.run()
    return at


def add_pet(at, name="Mochi"):
    """Fill in the pet form and click "Add pet"."""
    widget(at.text_input, "Pet name").set_value(name)
    widget(at.button, "Add pet").click()
    at.run()


def add_task(at, title, minutes, priority="HIGH", repeats="ONCE"):
    """Fill in the task form and click "Add task"."""
    widget(at.text_input, "Task title").set_value(title)
    widget(at.number_input, "Duration (minutes)").set_value(minutes)
    widget(at.selectbox, "Priority").set_value(priority)
    widget(at.selectbox, "Repeats").set_value(repeats)
    widget(at.button, "Add task").click()
    at.run()


def test_app_starts_with_no_pets(app):
    """The app loads without errors and asks for a pet first."""
    assert not app.exception
    assert app.info[0].value == "No pets yet. Add one above."


def test_add_pet_shows_it_in_the_list(app):
    """Adding a pet stores it on the owner and lists it on the page."""
    add_pet(app, "Mochi")

    assert [p.name for p in app.session_state.owner.pets] == ["Mochi"]
    assert any("Your pets: Mochi (dog)" in m.value for m in app.markdown)


def test_empty_pet_name_shows_error(app):
    """A blank pet name is refused with an error instead of adding a pet."""
    add_pet(app, "   ")

    assert app.session_state.owner.pets == []
    assert app.error[0].value == "Pet name can't be empty."


def test_add_task_stores_it_on_the_selected_pet(app):
    """The task form creates a Task with the chosen duration, priority and frequency."""
    add_pet(app)
    add_task(app, "Breakfast", 10, priority="LOW", repeats="DAILY")

    task = app.session_state.owner.pets[0].tasks[0]
    assert (task.title, task.duration_minutes) == ("Breakfast", 10)
    assert task.priority.name == "LOW"
    assert task.frequency is Frequency.DAILY
    assert len(app.dataframe) == 1  # the "Current tasks" table


def test_mark_complete_on_daily_task_adds_next_day(app):
    """Clicking "Mark complete" on a daily task finishes it and adds tomorrow's copy."""
    add_pet(app)
    add_task(app, "Breakfast", 10, repeats="DAILY")

    widget(app.button, "Mark complete").click()
    app.run()

    tasks = app.session_state.owner.pets[0].tasks
    assert [t.is_completed for t in tasks] == [True, False]
    assert app.success[0].value == (
        f"Done! Breakfast repeats daily; next due {tasks[1].due_date}."
    )


def test_generate_schedule_shows_plan_and_skipped_tasks(app):
    """The schedule lists tasks that fit, the total, and a warning for skipped tasks."""
    add_pet(app)
    widget(app.number_input, "Time available today (minutes)").set_value(30)
    app.run()
    add_task(app, "Give meds", 5, priority="HIGH")
    add_task(app, "Long walk", 60, priority="MEDIUM")

    widget(app.button, "Generate schedule").click()
    app.run()

    assert not app.exception
    assert app.success[-1].value == "Planned 1 task(s) in 5 of 30 minutes."
    assert app.warning[-1].value == "1 task(s) didn't fit in the remaining time:"
    skipped = app.table[-1].value
    assert list(skipped["Task"]) == ["Long walk"]


def test_generate_schedule_with_no_tasks(app):
    """With nothing to plan, the app says so instead of showing an empty schedule."""
    widget(app.button, "Generate schedule").click()
    app.run()

    assert app.info[-1].value == "There are no unfinished tasks to schedule."


def test_main_demo_runs(capsys):
    """main.py runs from start to finish and prints a schedule."""
    runpy.run_path(str(ROOT / "main.py"), run_name="__main__")

    assert "Today's Schedule for" in capsys.readouterr().out
