#!/usr/bin/env python3
import datetime as dt
import os
import time
from statistics import mean
from typing import List

import random

import requests

V_DRY = float(os.getenv("SENSOR_VOLTAGE_DRY", "2.80"))
V_WET = float(os.getenv("SENSOR_VOLTAGE_WET", "1.20"))
SAMPLE_INTERVAL_SECONDS = float(os.getenv("SENSOR_SAMPLE_INTERVAL_SECONDS", "1"))
SAMPLE_DURATION_SECONDS = int(os.getenv("SENSOR_SAMPLE_DURATION_SECONDS", "60"))

DIRECTUS_URL = os.getenv("DIRECTUS_URL", "http://flower-pi-directus:8055").rstrip("/")
DIRECTUS_TOKEN = os.getenv("DIRECTUS_TOKEN", "")
DIRECTUS_COLLECTION = os.getenv("DIRECTUS_COLLECTION", "plants_measured_values")
SENSOR_DEBUG = os.getenv("SENSOR_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}


def moisture_percent(voltage: float, v_dry: float, v_wet: float) -> float:
    value = (v_dry - voltage) / (v_dry - v_wet) * 100
    return max(0.0, min(100.0, value))


def read_samples(channel, duration_seconds: int, interval_seconds: float) -> dict:
    voltages: List[float] = []
    moistures: List[float] = []
    voltage_min = float("inf")
    voltage_max = float("-inf")

    start_time = time.monotonic()
    while time.monotonic() - start_time < duration_seconds:
        voltage = channel.voltage
        moisture = moisture_percent(voltage, V_DRY, V_WET)

        voltages.append(voltage)
        moistures.append(moisture)

        voltage_min = min(voltage_min, voltage)
        voltage_max = max(voltage_max, voltage)

        time.sleep(interval_seconds)

    return {
        "voltage_avg": mean(voltages),
        "voltage_min": voltage_min,
        "voltage_max": voltage_max,
        "moisture_avg": mean(moistures),
        "samples": len(voltages),
    }


def read_samples_debug(duration_seconds: int, interval_seconds: float) -> dict:
    sample_count = max(1, int(duration_seconds / max(interval_seconds, 0.1)))
    voltages = [random.uniform(min(V_DRY, V_WET), max(V_DRY, V_WET)) for _ in range(sample_count)]
    moistures = [moisture_percent(voltage, V_DRY, V_WET) for voltage in voltages]
    return {
        "voltage_avg": mean(voltages),
        "voltage_min": min(voltages),
        "voltage_max": max(voltages),
        "moisture_avg": mean(moistures),
        "samples": len(voltages),
    }


def upload_measurement(payload: dict) -> None:
    if not DIRECTUS_TOKEN:
        raise RuntimeError("DIRECTUS_TOKEN is not set.")

    url = f"{DIRECTUS_URL}/items/{DIRECTUS_COLLECTION}"
    headers = {"Authorization": f"Bearer {DIRECTUS_TOKEN}"}
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

    while True:
        if SENSOR_DEBUG:
            measurements = read_samples_debug(SAMPLE_DURATION_SECONDS, SAMPLE_INTERVAL_SECONDS)
        else:
            measurements = read_samples(channel, SAMPLE_DURATION_SECONDS, SAMPLE_INTERVAL_SECONDS)
        payload = {
            "measured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "moisture_percentage_average": round(measurements["moisture_avg"], 1),
            "voltage_average": round(measurements["voltage_avg"], 4),
            "voltage_min": round(measurements["voltage_min"], 4),
            "voltage_max": round(measurements["voltage_max"], 4),
            "sample_count": measurements["samples"],
        }

        try:
            upload_measurement(payload)
            print(f"Uploaded measurement: {payload}")
        except Exception as exc:
            print(f"Failed to upload measurement: {exc}. Payload: {payload}")


if __name__ == "__main__":
    main()
