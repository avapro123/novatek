import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .novatek_api import NovatekDevice

DOMAIN = "novatek"
PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data.get("host")
    password = entry.data.get("password")
    device = NovatekDevice(host, password)
    try:
        await hass.async_add_executor_job(device.Connect)
    except Exception as e:
        _LOGGER.error("Не удалось подключиться к устройству Novatek %s: %s", host, e)
        raise ConfigEntryNotReady from e

    async def async_update_data():
        try:
            data = await hass.async_add_executor_job(device.get_all_data)
            return data
        except Exception as err:
            _LOGGER.error("Ошибка получения данных с устройства Novatek: %s", err)
            raise UpdateFailed("Не удалось обновить данные устройства") from err

    update_interval = entry.options.get("scan_interval", 30)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"novatek_{host}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=update_interval),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "device": device,
        "coordinator": coordinator
    }

    async def on_hass_stop(event):
        _LOGGER.debug("Home Assistant останавливается, производится logout с устройства %s", host)
        await hass.async_add_executor_job(device.Logout)
    entry.async_on_unload(hass.bus.async_listen_once("homeassistant_stop", on_hass_stop))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if data:
            device = data.get("device")
            try:
                await hass.async_add_executor_job(device.Logout)
            except Exception:
                pass
    return unloaded
