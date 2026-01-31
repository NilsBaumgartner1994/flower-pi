#!/usr/bin/env python3
import json
import os
import time
import urllib.error
import urllib.request
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# --------------------
# Kalibrierung
# --------------------
V_DRY = 2.80   # Spannung bei trocken
V_WET = 1.20   # Spannung bei nass

# --------------------
# ADC Setup
# --------------------
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1   # ±4.096 V

chan = AnalogIn(ads, 0)

# --------------------
# Tracking
# --------------------
voltage_min = float("inf")
voltage_max = float("-inf")

DIRECTUS_URL = os.getenv("DIRECTUS_URL", "").rstrip("/")
DIRECTUS_EMAIL = os.getenv("DIRECTUS_EMAIL")
DIRECTUS_PASSWORD = os.getenv("DIRECTUS_PASSWORD")
DIRECTUS_PLANT_ID = os.getenv("DIRECTUS_PLANT_ID")
DIRECTUS_STATUS = os.getenv("DIRECTUS_STATUS", "published")
DIRECTUS_TIMEOUT = float(os.getenv("DIRECTUS_TIMEOUT", "10"))


def directus_login():
    if not DIRECTUS_URL or not DIRECTUS_EMAIL or not DIRECTUS_PASSWORD:
        return None

    payload = json.dumps(
        {"email": DIRECTUS_EMAIL, "password": DIRECTUS_PASSWORD}
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{DIRECTUS_URL}/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=DIRECTUS_TIMEOUT) as response:
        response_data = json.loads(response.read().decode("utf-8"))
    return response_data["data"]["access_token"]


def post_measurement(access_token, measurement):
    if not DIRECTUS_URL or not access_token:
        return

    payload = json.dumps(measurement).encode("utf-8")
    request = urllib.request.Request(
        f"{DIRECTUS_URL}/items/sensor_measurements",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
    )
    with urllib.request.urlopen(request, timeout=DIRECTUS_TIMEOUT):
        pass


def moisture_percent(voltage, v_dry, v_wet):
    value = (v_dry - voltage) / (v_dry - v_wet) * 100
    return max(0.0, min(100.0, value))


# --------------------
# Loop
# --------------------
access_token = directus_login()

while True:
    voltage = chan.voltage

    voltage_min = min(voltage_min, voltage)
    voltage_max = max(voltage_max, voltage)

    moisture = moisture_percent(voltage, V_DRY, V_WET)

    output = {
        "voltage_current": round(voltage, 4),
        "voltage_min": round(voltage_min, 4),
        "voltage_max": round(voltage_max, 4),
        "moisture_percentage": round(moisture, 1)
    }

    print(json.dumps(output))

    payload = {
        **output,
        "data_raw": json.dumps(output),
        "status": DIRECTUS_STATUS,
    }
    if DIRECTUS_PLANT_ID:
        payload["plant"] = DIRECTUS_PLANT_ID

    try:
        post_measurement(access_token, payload)
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            try:
                access_token = directus_login()
                post_measurement(access_token, payload)
            except (urllib.error.HTTPError, urllib.error.URLError) as auth_exc:
                print(f"Directus auth failed: {auth_exc}")
        else:
            print(f"Directus request failed: {exc}")
    except urllib.error.URLError as exc:
        print(f"Directus request failed: {exc}")

    time.sleep(1.0)
