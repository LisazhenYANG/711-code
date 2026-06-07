import os
import unittest
from unittest.mock import patch

from backend.services import weather_api


class WeatherServiceTest(unittest.TestCase):
    def test_fetch_weather_falls_back_without_api_key(self):
        with patch.dict(os.environ, {}, clear=False):
            payload = weather_api.fetch_weather("上海")

        self.assertEqual(payload["city"], "上海")
        self.assertEqual(payload["condition"], "多云转晴")
        self.assertEqual(payload["source"], "mock")

    def test_fetch_weather_uses_qweather_response_when_configured(self):
        qweather_payload = {
            "code": "200",
            "now": {
                "text": "晴",
                "temp": "27",
                "feelsLike": "29",
                "windDir": "东南风",
            },
        }

        with patch.dict(
            os.environ,
            {
                "WEATHER_API_KEY": "test-key",
                "WEATHER_API_BASE_URL": "https://mock.qweather.com",
            },
            clear=False,
        ):
            with patch.object(weather_api, "_lookup_location", return_value=("101020100", "上海")):
                with patch.object(weather_api, "_get_json", return_value=qweather_payload):
                    payload = weather_api.fetch_weather("上海")

        self.assertEqual(payload["city"], "上海")
        self.assertEqual(payload["condition"], "晴")
        self.assertEqual(payload["temp"], "27°C")
        self.assertEqual(payload["feels_like"], "29°C")
        self.assertEqual(payload["source"], "qweather")


if __name__ == "__main__":
    unittest.main()
