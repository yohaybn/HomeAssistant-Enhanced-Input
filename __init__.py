
import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_NAME
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store

DOMAIN = "enhanced_input"
SERVICE_CREATE_INPUT_TEXT = "create_input_text"
SERVICE_DELETE_INPUT_TEXT = "delete_input_text"
CONF_TEXT = "text"
CONF_TITLE = "title"
DEFAULT_NAME = "Enhanced Input"
STORAGE_KEY = "enhanced_input_storage"
STORAGE_VERSION = 1
DEFAULT_NAME = "Enhanced Input"

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored_data = await store.async_load() or {}
    component = EntityComponent(_LOGGER, DOMAIN, hass)

    async def save_data():
        await store.async_save(stored_data)

    entities = []
    existing_entities = set(hass.states.async_entity_ids())
    for entity_id, data in list(stored_data.items()):
        if entity_id in existing_entities:
            continue
        if not data:
            stored_data.pop(entity_id, None)  # Ensure deleted entities are not restored
            continue
        try:
            name = entity_id.split(".")[-1].replace("_", " ").title()
            title = data.get("title", name)
            entity = LongTextInputEntity(name, title, data.get("text", ""), stored_data, save_data)
            hass.data[DOMAIN][entry.entry_id][entity_id] = entity
            entities.append(entity)
        except Exception as e:
            _LOGGER.warning(f"{e}")

    await component.async_add_entities(entities)

    async def handle_create_input_text(call: ServiceCall):
        name = call.data.get(CONF_NAME, DEFAULT_NAME)
        text = call.data.get(CONF_TEXT, "")
        title = call.data.get(CONF_TITLE, name)
        entity_id = f"{DOMAIN}.{name.lower().replace(' ', '_')}"

        entry_id = next(iter(hass.data[DOMAIN]), None)
        if not entry_id:
            _LOGGER.warning("No config entry found. Please set up the integration first.")
            return False

        if entity_id in hass.data[DOMAIN][entry_id]:
            entity = hass.data[DOMAIN][entry_id][entity_id]
            entity.update_text(text)
            entity.update_title(title)
            entity.async_write_ha_state()
        else:
            entity = LongTextInputEntity(name, title, text, stored_data, save_data)
            hass.data[DOMAIN][entry_id][entity_id] = entity
            await component.async_add_entities([entity])

    async def handle_delete_input_text(call: ServiceCall):
        name = call.data.get(CONF_NAME)
        entity_id = f"{DOMAIN}.{name.lower().replace(' ', '_')}"
        entry_id = next(iter(hass.data[DOMAIN]), None)
        if not entry_id:
            _LOGGER.warning("No config entry found. Please set up the integration first.")
            return False

        if entity_id in hass.data[DOMAIN][entry_id]:
            entity = hass.data[DOMAIN][entry_id].pop(entity_id)
            stored_data.pop(entity_id, None)
            await save_data()
            await hass.states.async_remove(entity_id)

    hass.services.async_register(DOMAIN, SERVICE_CREATE_INPUT_TEXT, handle_create_input_text)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_INPUT_TEXT, handle_delete_input_text)

    return True

async def async_setup(hass: HomeAssistant, config: ConfigType):
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored_data = await store.async_load() or {}

    if entry.entry_id in hass.data[DOMAIN]:
        for entity_id in list(hass.data[DOMAIN][entry.entry_id]):
            hass.data[DOMAIN][entry.entry_id].pop(entity_id, None)
            stored_data.pop(entity_id, None)
            await hass.states.async_remove(entity_id)
        await store.async_save(stored_data)
        hass.data[DOMAIN].pop(entry.entry_id)
    return True

class LongTextInputEntity(Entity):
    def __init__(self, name: str, title: str, text: str, stored_data, save_data):
        self._name = name
        self._title = title
        self._text = text
        self.entity_id = f"{DOMAIN}.{name.lower().replace(' ', '_')}"
        self._attr_unique_id = f"long_text_input_{name.lower().replace(' ', '_')}"
        self._stored_data = stored_data
        self._save_data = save_data

        if self.entity_id in stored_data:
            self._text = stored_data[self.entity_id].get("text", "")
            self._title = stored_data[self.entity_id].get("title", name)

    async def async_added_to_hass(self):
        self._stored_data[self.entity_id] = {"title": self._title, "text": self._text}
        await self._save_data()

    async def async_will_remove_from_hass(self):
        if self.entity_id in self._stored_data:
            self._stored_data.pop(self.entity_id, None)
            await self._save_data()
            await self.hass.states.async_remove(self.entity_id)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._title

    @property
    def extra_state_attributes(self):
        return {"long_text": self._text, "length": len(self._text)}

    def update_text(self, new_text: str):
        self._text = new_text
        self._stored_data[self.entity_id]["text"] = new_text
        self.hass.async_create_task(self._save_data())

    def update_title(self, new_title: str):
        self._title = new_title
        self._stored_data[self.entity_id]["title"] = new_title
        self.hass.async_create_task(self._save_data())