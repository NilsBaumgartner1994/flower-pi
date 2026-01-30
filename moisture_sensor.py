#!/usr/bin/env python3
import time
import json
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


def moisture_percent(voltage, v_dry, v_wet):
    value = (v_dry - voltage) / (v_dry - v_wet) * 100
    return max(0.0, min(100.0, value))


# --------------------
# Loop
# --------------------
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

    time.sleep(1.0)
