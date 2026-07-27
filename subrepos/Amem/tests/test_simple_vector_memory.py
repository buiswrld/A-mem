from agentic_memory.simple_vector_memory import SimpleVectorMemory


def test_add_note_and_search_by_meaning(temp_db_dir):
    memory = SimpleVectorMemory(
        directory=str(temp_db_dir), collection_name="simple_memory_test"
    )
    stored_id = memory.add_note(
        "A patient needs follow-up for medication side effects.",
        metadata={"source": "demo", "run_id": "smoke-test"},
        note_id="follow-up-note",
    )
    memory.add_note(
        "The project meeting is scheduled for Tuesday afternoon.",
        note_id="meeting-note",
    )

    matches = memory.search("How should we monitor a drug reaction?", k=1)

    assert stored_id == "follow-up-note"
    assert matches[0]["id"] == "follow-up-note"
    assert matches[0]["metadata"]["source"] == "demo"


def test_notes_persist_when_a_new_memory_object_reconnects(temp_db_dir):
    first_session = SimpleVectorMemory(
        directory=str(temp_db_dir), collection_name="persistent_memory_test"
    )
    first_session.add_note("Persistent note", note_id="persistent-note")

    second_session = SimpleVectorMemory(
        directory=str(temp_db_dir), collection_name="persistent_memory_test"
    )

    assert second_session.count() == 1
    assert second_session.search("persistent", k=1)[0]["id"] == "persistent-note"
