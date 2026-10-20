from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    """mark_complete() should flip is_completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30)
    assert task.is_completed is False

    task.mark_complete()

    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    """add_task() should increase the pet's task count by one."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Feed breakfast", duration_minutes=10))

    assert len(pet.tasks) == 1
