#!/usr/bin/env bash
set -euo pipefail

# Docker Installation fuer Ubuntu 22.04
# Quelle: https://docs.docker.com/engine/install/ubuntu/

# 1. Alte Versionen entfernen (falls vorhanden)
sudo apt-get remove -y docker docker-engine docker.io containerd runc || true

# 2. Abhaengigkeiten installieren
sudo apt-get update
sudo apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

# 3. Docker GPG Key hinzufuegen
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 4. Docker Repository hinzufuegen
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Docker installieren
sudo apt-get update
sudo apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

# 6. Docker Gruppe setzen (optional, erfordert neues Login)
if ! getent group docker >/dev/null; then
  sudo groupadd docker
fi
sudo usermod -aG docker "$USER"

echo "Docker installiert. Bitte einmal ab- und wieder anmelden, damit die Gruppenrechte wirken."
