import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_NAME
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store
from homeassistant.helpers.device_registry import DeviceInfo  # For device_info
from typing import Any  # For type hinting

DOMAIN = "enhanced_input"
SERVICE_CREATE_INPUT_TEXT = "create_input_text"
SERVICE_DELETE_INPUT_TEXT = "delete_input_text"
CONF_TEXT = "text"
CONF_TITLE = "title"
STORAGE_KEY = "enhanced_input_storage"
STORAGE_VERSION = 1
DEFAULT_NAME = "Enhanced Input"

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the enhanced_input component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up enhanced_input from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if "component" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["component"] = EntityComponent(_LOGGER, DOMAIN, hass)
    component: EntityComponent = hass.data[DOMAIN]["component"]

    hass.data[DOMAIN][entry.entry_id] = {}

    store = Store[dict[str, Any]](hass, STORAGE_VERSION, STORAGE_KEY)
    loaded_data_from_store = await store.async_load()
    stored_data_dict: dict[str, Any] = (
        loaded_data_from_store if loaded_data_from_store is not None else {}
    )

    async def save_persistent_data():
        await store.async_save(stored_data_dict)

    entities_to_add = []
    for entity_id_str, entity_data_dict_any in list(stored_data_dict.items()):
        if not isinstance(entity_data_dict_any, dict):
            _LOGGER.warning(
                f"Removing invalid (non-dict) stored data for {entity_id_str}"
            )
            stored_data_dict.pop(entity_id_str, None)
            continue

        entity_data_dict: dict[str, Any] = entity_data_dict_any

        object_id = entity_id_str.split(".")[-1]
        constructor_name_arg = object_id.replace("_", " ").title()

        title_for_state_and_maybe_name = entity_data_dict.get(
            "title", constructor_name_arg
        )
        text_value = entity_data_dict.get("text", "")

        try:
            entity = LongTextInputEntity(
                hass,
                entry.entry_id,
                constructor_name_arg,
                title_for_state_and_maybe_name,
                text_value,
                stored_data_dict,
                save_persistent_data,
            )
            hass.data[DOMAIN][entry.entry_id][entity.entity_id] = entity
            entities_to_add.append(entity)
        except Exception as e:
            _LOGGER.error(
                f"Error loading entity {entity_id_str} from storage: {e}", exc_info=True
            )

    if entities_to_add:
        await component.async_add_entities(entities_to_add)

    await save_persistent_data()

    async def handle_create_input_text(call: ServiceCall):
        name_arg = call.data.get(CONF_NAME, DEFAULT_NAME)
        text_arg = call.data.get(CONF_TEXT, "")
        title_arg = call.data.get(CONF_TITLE, name_arg)

        object_id = name_arg.lower().replace(" ", "_")
        target_entity_id = f"{DOMAIN}.{object_id}"

        entry_entities_dict = hass.data[DOMAIN][entry.entry_id]

        if target_entity_id in entry_entities_dict:
            entity: LongTextInputEntity = entry_entities_dict[target_entity_id]
            _LOGGER.debug(f"Updating existing entity: {target_entity_id}")
            entity.update_text(text_arg)
            entity.update_title(title_arg)
            entity.async_write_ha_state()
        else:
            _LOGGER.debug(
                f"Creating new entity: {target_entity_id} with name '{name_arg}' and title '{title_arg}'"
            )
            entity = LongTextInputEntity(
                hass,
                entry.entry_id,
                name_arg,
                title_arg,
                text_arg,
                stored_data_dict,  # Pass the mutable dict
                save_persistent_data,  # Pass the save function
            )
            entry_entities_dict[entity.entity_id] = entity
            await component.async_add_entities([entity])

    async def handle_delete_input_text(call: ServiceCall):
        name_param = call.data.get(CONF_NAME)
        if not name_param:
            _LOGGER.error(f"{SERVICE_DELETE_INPUT_TEXT} requires '{CONF_NAME}'")
            return

        object_id_to_delete = name_param.lower().replace(" ", "_")
        entity_id_to_delete = f"{DOMAIN}.{object_id_to_delete}"

        entity_instance_to_delete = None
        source_entry_id_for_entity = None
        for eid_key, entities_in_entry in hass.data[DOMAIN].items():
            if eid_key == "component" or not isinstance(entities_in_entry, dict):
                continue
            if entity_id_to_delete in entities_in_entry:
                entity_instance_to_delete = entities_in_entry[entity_id_to_delete]
                source_entry_id_for_entity = eid_key
                break

        if entity_instance_to_delete and source_entry_id_for_entity:
            _LOGGER.info(f"Deleting entity: {entity_id_to_delete}")
            hass.data[DOMAIN][source_entry_id_for_entity].pop(entity_id_to_delete, None)
            await component.async_remove_entity(entity_id_to_delete)
        else:
            _LOGGER.warning(
                f"Entity {entity_id_to_delete} not found in active entities."
            )
            if entity_id_to_delete in stored_data_dict:
                _LOGGER.info(
                    f"Removing orphaned entity {entity_id_to_delete} from storage."
                )
                stored_data_dict.pop(entity_id_to_delete, None)
                await save_persistent_data()

    hass.services.async_register(
        DOMAIN, SERVICE_CREATE_INPUT_TEXT, handle_create_input_text
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_INPUT_TEXT, handle_delete_input_text
    )

    entry.async_on_unload(
        lambda: hass.services.async_remove(DOMAIN, SERVICE_CREATE_INPUT_TEXT)
    )
    entry.async_on_unload(
        lambda: hass.services.async_remove(DOMAIN, SERVICE_DELETE_INPUT_TEXT)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    component: EntityComponent | None = hass.data[DOMAIN].get("component")
    entry_entities_dict = hass.data[DOMAIN].get(entry.entry_id)

    entities_to_remove_ids = []
    if isinstance(entry_entities_dict, dict):
        entities_to_remove_ids = list(entry_entities_dict.keys())

    if component and entities_to_remove_ids:
        for entity_id_to_remove in entities_to_remove_ids:
            _LOGGER.debug(
                f"Removing entity {entity_id_to_remove} during unload of entry {entry.entry_id}."
            )
            await component.async_remove_entity(entity_id_to_remove)
            # The entity's async_will_remove_from_hass method will handle its removal
            # from the shared stored_data_dict and trigger a save.

    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    return True


class LongTextInputEntity(Entity):
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry_id: str,
        name: str,
        title: str,
        text: str,
        stored_data_ref: dict[str, Any],
        save_data_func: callable,
    ):
        """Initialize the long text input entity."""
        self.hass = hass
        self._config_entry_id = config_entry_id

        self._name = name
        self._title = title
        self._text = text

        self._stored_data_ref = stored_data_ref
        self._save_data_func = save_data_func

        object_id_part = self._name.lower().replace(" ", "_")
        self.entity_id = f"{DOMAIN}.{object_id_part}"
        self._attr_unique_id = f"{DOMAIN}_{object_id_part}"

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._title

    @property
    def extra_state_attributes(self):
        return {"long_text": self._text, "length": len(self._text)}

    @property
    def device_info(self) -> DeviceInfo:
        config_entry = self.hass.config_entries.async_get_entry(self._config_entry_id)
        device_name = DEFAULT_NAME  # Fallback
        if config_entry:
            device_name = (
                f"Enhanced Input ({config_entry.title or self._config_entry_id})"
            )

        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry_id)},
            name=device_name,
            manufacturer="Enhanced Input Integration",
            model="Long Text Storage",  # Optional
            # sw_version= # Optional, e.g., from manifest.json version
        )

    async def async_added_to_hass(self):
        _LOGGER.debug(f"Entity {self.entity_id} added. Persisting current state.")
        self._stored_data_ref[self.entity_id] = {
            "title": self._title,
            "text": self._text,
            # If self._name (friendly name) could change and needs persisting, add it here.
            # "name_for_reload": self._name # To reconstruct on reload if needed
        }
        await self._save_data_func()

    async def async_will_remove_from_hass(self):
        _LOGGER.debug(
            f"Entity {self.entity_id} will be removed. Removing from storage."
        )
        if self.entity_id in self._stored_data_ref:
            self._stored_data_ref.pop(self.entity_id, None)
            await self._save_data_func()

    def update_text(self, new_text: str):
        if self._text == new_text:
            return
        self._text = new_text
        # Ensure this entity's data exists in the shared dictionary
        if self.entity_id not in self._stored_data_ref:
            self._stored_data_ref[self.entity_id] = {}  # Initialize if somehow missing
        self._stored_data_ref[self.entity_id]["text"] = new_text
        self._stored_data_ref[self.entity_id]["title"] = (
            self._title
        )  # Ensure title is also current

        self.hass.async_create_task(self._save_data_func())

    def update_title(self, new_title: str):
        if self._title == new_title:
            return
        self._title = new_title
        if self.entity_id not in self._stored_data_ref:
            self._stored_data_ref[self.entity_id] = {}  # Initialize if somehow missing
        self._stored_data_ref[self.entity_id]["title"] = new_title
        self._stored_data_ref[self.entity_id]["text"] = self._text

        self.hass.async_create_task(self._save_data_func())
