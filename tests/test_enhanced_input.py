import pytest

from custom_components.enhanced_input import LongTextInputEntity
from custom_components.enhanced_input.helpers import (
    migrate_storage,
    slugify_name,
    to_text,
)


@pytest.mark.parametrize(
    "name",
    ["AI Answer", "ai-answer", "ai_answer", " Ai  Answer ", "AI.Answer"],
)
def test_same_name_same_slug(name):
    assert slugify_name(name) == "ai_answer"


def test_slug_is_valid_object_id_and_never_empty():
    assert slugify_name("---") == "enhanced_input"
    assert slugify_name(123) == "123"


def test_to_text_coerces_numbers_and_none():
    assert to_text(5) == "5"
    assert to_text(None) == ""
    assert to_text("x") == "x"


def test_entity_with_int_text_does_not_crash():
    """Issue #4: TypeError: object of type 'int' has no len()."""
    ent = LongTextInputEntity(None, "e1", "Halo Tickets", "t", 12345, {}, None)
    assert ent.extra_state_attributes == {"long_text": "12345", "length": 5}


def test_entity_id_and_unique_id_are_stable_for_name_variants():
    """Issue #1: 'ai-answer' and 'Ai Answer' must not become different entities."""
    a = LongTextInputEntity(None, "e1", "ai-answer", "t", "", {}, None)
    b = LongTextInputEntity(None, "e1", "Ai Answer", "t", "", {}, None)
    assert a.entity_id == b.entity_id == "enhanced_input.ai_answer"
    assert a.unique_id == b.unique_id == "enhanced_input_ai_answer"


def test_name_is_not_recomputed_with_suffix_on_reload():
    ent = LongTextInputEntity(None, "e1", "Halo Tickets", "t", "x", {}, None)
    assert ent.entity_id == "enhanced_input.halo_tickets"
    assert ent.name == "Halo Tickets"


def test_migration_drops_duplicate_chain_when_base_exists():
    data = {
        "enhanced_input.ai_answer": {"text": "a"},
        "enhanced_input.ai_answer_2": {"text": "a"},
        "enhanced_input.ai_answer_2_2": {},
        "enhanced_input.ai_answer_2_2_2": {},
        "enhanced_input.other": {"text": "o"},
    }
    new, removed = migrate_storage(data)
    assert set(new) == {
        "enhanced_input.ai_answer",
        "enhanced_input.ai_answer_2",
        "enhanced_input.other",
    }
    assert set(removed) == {
        "enhanced_input.ai_answer_2_2",
        "enhanced_input.ai_answer_2_2_2",
    }


def test_migration_renames_chain_without_base():
    data = {"enhanced_input.halo_tickets_2_2_2_2": {"text": "keep"}}
    new, removed = migrate_storage(data)
    assert new == {"enhanced_input.halo_tickets": {"text": "keep"}}
    assert removed == ["enhanced_input.halo_tickets_2_2_2_2"]


def test_migration_keeps_legit_names():
    data = {"enhanced_input.room_2": {}, "enhanced_input.room": {}, "enhanced_input.a_20": {}}
    new, removed = migrate_storage(data)
    assert new == data and removed == []
