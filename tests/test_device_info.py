from custom_components.enhanced_input import LongTextInputEntity


def test_entity_has_no_device_info():
    """Issue #5: entities are added via EntityComponent (no config entry on the
    platform), so they must not declare device_info; HA 2027.8 rejects it."""
    ent = LongTextInputEntity(None, "e1", "x", "t", "", {}, None)
    assert getattr(ent, "device_info", None) is None
