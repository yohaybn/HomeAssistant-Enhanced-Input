"""Stub the few Home Assistant modules enhanced_input imports so tests run without HA."""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _mod(name, **attrs):
    m = types.ModuleType(name)
    m.__dict__.update(attrs)
    sys.modules[name] = m
    return m


class _Entity:
    pass


class _Generic:
    def __class_getitem__(cls, item):
        return cls


_mod("homeassistant")
_mod("homeassistant.core", HomeAssistant=object, ServiceCall=object)
_mod("homeassistant.helpers")
_mod("homeassistant.helpers.entity", Entity=_Entity)
_mod("homeassistant.helpers.entity_component", EntityComponent=object)
_mod("homeassistant.helpers.typing", ConfigType=dict)
_mod("homeassistant.const", CONF_NAME="name")
_mod("homeassistant.config_entries", ConfigEntry=object)
_mod("homeassistant.helpers.storage", Store=_Generic)
_mod("homeassistant.helpers.device_registry", DeviceInfo=dict)
_mod("homeassistant.helpers.entity_registry")
sys.modules["homeassistant.helpers"].entity_registry = sys.modules[
    "homeassistant.helpers.entity_registry"
]
