#!/usr/bin/env bash
set -euo pipefail

# ADS1115 Setup unter Ubuntu auf dem Raspberry Pi
# Diese Schritte folgen der Readme und bereiten I2C + Python-Abhängigkeiten vor.

# 1. System aktualisieren
sudo apt update
sudo apt upgrade

# 2. I2C aktivieren (Ubuntu-spezifisch)
# Ubuntu verwendet kein raspi-config. I2C wird über den Device Tree aktiviert.
sudo nano /boot/firmware/config.txt

# Sicherstellen, dass folgende Zeile vorhanden ist:
# dtparam=i2c_arm=on

# Neustart
sudo reboot

# 3. I2C prüfen und Tools installieren
sudo apt install -y i2c-tools
ls /dev/i2c-*

# I2C-Geräte scannen (ADS1115 Standardadresse: 48)
sudo i2cdetect -y 1

# 4. Python-Abhängigkeiten installieren
sudo apt install -y python3-pip python3-smbus python3-rpi.gpio

# 5. Adafruit-Bibliotheken installieren
pip3 install --upgrade adafruit-blinka
pip3 install adafruit-circuitpython-ads1x15

# Falls Ubuntu 22.04+ eine Warnung ausgibt:
# pip3 install --break-system-packages adafruit-blinka adafruit-circuitpython-ads1x15
