import base64
import hashlib
import requests

class NovatekDevice:
    """
    Класс для работы с устройствами Novatek-Electro (например, EM-125, EM-126T, EM-129).
    Реализует авторизацию и получение данных.
    """
    # Сопоставление device_id с наименованием модели
    MODELS = {
        243: "EM-125",
        293: "EM-126T",
        255: "EM-125S",
        285: "EM-126TS",
        271: "EM-129"
    }

    def __init__(self, host: str, password: str):
        """Инициализация устройства с указанием IP/хоста и пароля (в открытом виде)."""
        self._host = host
        if not self._host.startswith("http"):
            self._url = "http://" + self._host
        else:
            self._url = self._host
        self._password = password
        self._sid = None
        self._endpoint = None
        self.model = None
        self.device_name = None

    def Connect(self):
        """Вход в систему и получение сессионного идентификатора (SID). При неудаче возбуждает исключение."""
        r = requests.get(f"{self._url}/api/login?device_info")
        r.raise_for_status()
        data = r.json()
        if data.get("STATUS") != "OK":
            raise ConnectionAbortedError("Запрос информации об устройстве завершился с ошибкой")
        device_id = data.get("device_id")
        prefix = self.MODELS.get(device_id, "")
        try:
            user_info_b64 = data.get("user_info", "")
            self.device_name = base64.b64decode(user_info_b64).decode("utf-8") if user_info_b64 else None
        except Exception:
            self.device_name = None
        self.model = prefix

        r = requests.get(f"{self._url}/api/login?salt")
        r.raise_for_status()
        data = r.json()
        if data.get("STATUS") != "OK":
            raise ConnectionAbortedError("Не удалось получить SALT от устройства")
        salt = data.get("SALT", "")

        sha = hashlib.sha1()
        hash_input = f"{prefix}{self._password}{salt}"
        sha.update(hash_input.encode("utf-8"))
        hashed_password = sha.hexdigest()

        r = requests.get(f"{self._url}/api/login?login={hashed_password}")
        r.raise_for_status()
        data = r.json()
        if data.get("STATUS") != "OK":
            raise ConnectionAbortedError("Ошибка авторизации: неверный пароль или ошибка сессии")
        self._sid = data.get("SID")
        self._endpoint = f"{self._url}/{self._sid}"

    def Logout(self):
        """Выход из системы для освобождения сессии."""
        if self._sid:
            try:
                requests.get(f"{self._url}/api/login?logout={self._sid}")
            except Exception:
                pass
        self._sid = None
        self._endpoint = None

    def _get_value(self, endpoint: str) -> float:
        """Внутренняя функция для GET-запроса к API. Возвращает числовое значение."""
        r = requests.get(f"{self._endpoint}{endpoint}")
        r.raise_for_status()
        data = r.json()
        if data.get("STATUS") != "OK":
            raise ConnectionAbortedError("Устройство вернуло статус ошибки")
        for key, value in data.items():
            if key != "STATUS":
                return float(value)
        raise ConnectionAbortedError("Ответ не содержит данных")

    def Voltage(self) -> float:
        """Возвращает текущее значение напряжения (в вольтах). (API возвращает значение в V*10)"""
        val = self._get_value("/api/all/get?volt_msr")
        return val / 10.0

    def Current(self) -> float:
        """Возвращает текущее значение тока (в амперах). (API возвращает значение в A*100)"""
        val = self._get_value("/api/all/get?cur_msr")
        return val / 100.0

    def Frequency(self) -> float:
        """Возвращает значение частоты сети (в Герцах). (API возвращает значение в Hz*100)"""
        val = self._get_value("/api/all/get?freq_msr")
        return val / 100.0

    def ActivePower(self) -> float:
        """Возвращает активную мощность (W)."""
        return self._get_value("/api/all/get?powa_msr")

    def FullPower(self) -> float:
        """Возвращает полную (апп. или полную) мощность (W)."""
        return self._get_value("/api/all/get?pows_msr")

    def ActiveEnergy(self) -> float:
        """Возвращает активную энергию (Wh)."""
        return self._get_value("/api/all/get?enrga_msr")

    def FullEnergy(self) -> float:
        """Возвращает полную (апп.) энергию (Wh)."""
        return self._get_value("/api/all/get?enrgs_msr")

    def get_all_data(self) -> dict:
        """Возвращает все измеряемые параметры в виде словаря."""
        try:
            return {
                "voltage": self.Voltage(),
                "current": self.Current(),
                "frequency": self.Frequency(),
                "active_power": self.ActivePower(),
                "full_power": self.FullPower(),
                "active_energy": self.ActiveEnergy(),
                "full_energy": self.FullEnergy()
            }
        except Exception:
            self.Connect()
            return {
                "voltage": self.Voltage(),
                "current": self.Current(),
                "frequency": self.Frequency(),
                "active_power": self.ActivePower(),
                "full_power": self.FullPower(),
                "active_energy": self.ActiveEnergy(),
                "full_energy": self.FullEnergy()
            }
