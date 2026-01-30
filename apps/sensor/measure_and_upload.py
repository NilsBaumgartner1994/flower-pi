#!/usr/bin/env python3
import datetime as dt
import os
import time
from collections import deque
from statistics import mean
from typing import Deque, Dict, Optional, Tuple

import random

import requests

V_DRY = float(os.getenv("SENSOR_VOLTAGE_DRY", "2.80"))
V_WET = float(os.getenv("SENSOR_VOLTAGE_WET", "1.20"))
SAMPLE_INTERVAL_SECONDS = float(os.getenv("SENSOR_SAMPLE_INTERVAL_SECONDS", "5"))
AVERAGE_WINDOW_SECONDS = int(
    os.getenv("SENSOR_AVERAGE_WINDOW_SECONDS", os.getenv("SENSOR_SAMPLE_DURATION_SECONDS", "60"))
)

DIRECTUS_URL = os.getenv("DIRECTUS_URL", "http://flower-pi-directus:8055").rstrip("/")
DIRECTUS_COLLECTION = os.getenv("DIRECTUS_COLLECTION", "plants_measured_values")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SENSOR_DEBUG = os.getenv("SENSOR_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}

_DIRECTUS_TOKEN: Optional[str] = None
_DIRECTUS_TOKEN_EXPIRES_AT: Optional[float] = None


def moisture_percent(voltage: float, v_dry: float, v_wet: float) -> float:
    value = (v_dry - voltage) / (v_dry - v_wet) * 100
    return max(0.0, min(100.0, value))


def read_sample(channel) -> Tuple[float, float]:
    voltage = channel.voltage
    moisture = moisture_percent(voltage, V_DRY, V_WET)
    return voltage, moisture


def read_sample_debug() -> Tuple[float, float]:
    voltage = random.uniform(min(V_DRY, V_WET), max(V_DRY, V_WET))
    moisture = moisture_percent(voltage, V_DRY, V_WET)
    return voltage, moisture


def build_window_stats(samples: Deque[Tuple[float, float, float]]) -> Dict[str, float]:
    voltages = [sample[1] for sample in samples]
    moistures = [sample[2] for sample in samples]
    return {
        "voltage_avg": mean(voltages),
        "voltage_min": min(voltages),
        "voltage_max": max(voltages),
        "moisture_avg": mean(moistures),
        "samples": len(samples),
    }


def login_directus() -> str:
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        raise RuntimeError("ADMIN_EMAIL/ADMIN_PASSWORD must be set for Directus login.")

    url = f"{DIRECTUS_URL}/auth/login"
    payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    response = requests.post(url, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json().get("data", {})
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Directus login failed: missing access_token.")
    expires = data.get("expires")
    if isinstance(expires, (int, float)):
        global _DIRECTUS_TOKEN_EXPIRES_AT
        _DIRECTUS_TOKEN_EXPIRES_AT = time.time() + float(expires) - 30
    return token


def get_directus_token() -> str:
    global _DIRECTUS_TOKEN
    if _DIRECTUS_TOKEN:
        if _DIRECTUS_TOKEN_EXPIRES_AT is None:
            return _DIRECTUS_TOKEN
        if time.time() < _DIRECTUS_TOKEN_EXPIRES_AT:
            return _DIRECTUS_TOKEN
    _DIRECTUS_TOKEN = login_directus()
    return _DIRECTUS_TOKEN


def upload_measurement(payload: dict) -> None:
    token = get_directus_token()
    url = f"{DIRECTUS_URL}/items/{DIRECTUS_COLLECTION}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, json=payload, headers=headers, timeout=20)
    response.raise_for_status()


def main() -> None:
    channel = None
    if not SENSOR_DEBUG:
        import board
        import busio
        import adafruit_ads1x15.ads1115 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn

        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        ads.gain = 1
        channel = AnalogIn(ads, 0)

    samples: Deque[Tuple[float, float, float]] = deque()
    while True:
        timestamp = time.time()
        if SENSOR_DEBUG:
            voltage, moisture = read_sample_debug()
        else:
            voltage, moisture = read_sample(channel)
        samples.append((timestamp, voltage, moisture))

        window_start = timestamp - AVERAGE_WINDOW_SECONDS
        while samples and samples[0][0] < window_start:
            samples.popleft()

        if samples:
            measurements = build_window_stats(samples)
            payload = {
                "measured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "moisture_percentage_average": round(measurements["moisture_avg"], 1),
            }

            try:
                upload_measurement(payload)
                print(f"Uploaded measurement: {payload}")
            except Exception as exc:
                print(f"Failed to upload measurement: {exc}. Payload: {payload}")

        time.sleep(SAMPLE_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
