import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .novatek_api import NovatekDevice
from . import DOMAIN

class NovatekConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow для интеграции Novatek (EM-129 и подобных устройств)."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            existing = any(entry.data.get("host") == user_input["host"] for entry in self._async_current_entries())
            if existing:
                return self.async_abort(reason="already_configured")
            device = NovatekDevice(user_input["host"], user_input["password"])
            try:
                await self.hass.async_add_executor_job(device.Connect)
            except Exception as e:
                if isinstance(e, ConnectionAbortedError):
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
            else:
                device_name = device.device_name or ""
                model = device.model or "device"
                host = user_input["host"]
                name = user_input.get("name")
                if name:
                    title = name
                else:
                    if device_name and device_name != model:
                        title = device_name
                    else:
                        title = f"{model} ({host})"
                data = {
                    "host": user_input["host"],
                    "password": user_input["password"]
                }
                return self.async_create_entry(title=title, data=data)
        data_schema = vol.Schema({
            vol.Required("host"): str,
            vol.Required("password"): str,
            vol.Optional("name"): str
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NovatekOptionsFlow(config_entry)

class NovatekOptionsFlow(config_entries.OptionsFlow):
    """Опции интеграции (например, интервал опроса)."""
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        data_schema = vol.Schema({
            vol.Optional("scan_interval", default=self.config_entry.options.get("scan_interval", 30)): int
        })
        return self.async_show_form(step_id="init", data_schema=data_schema)
