from homeassistant import config_entries
import voluptuous as vol
DOMAIN = "enhanced_input"
class EnhancedInputConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        existing_entry = self._async_current_entries()
        if existing_entry:
            return self.async_abort(reason="already_configured")
        if user_input is not None:
            return self.async_create_entry(title="Enhanced Input", data={})

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))