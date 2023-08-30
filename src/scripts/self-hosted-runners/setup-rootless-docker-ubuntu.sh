#!/bin/bash

# Exit on error
set -e

# Install required packages only if they aren't already installed
sudo apt update
# Check for curl
if ! command -v curl &> /dev/null; then
  echo "Installing curl..."
  sudo apt install -y curl
fi

# Check for iptables
if ! command -v iptables &> /dev/null; then
  echo "Installing iptables..."
  sudo apt install -y iptables
fi

sudo apt install -y uidmap

# Download Docker installation script
echo "Installing Docker in rootless mode..."
curl -fsSL https://get.docker.com/rootless | sh

# Set environment variables
echo "Updating environment variables..."
USER_NAME=$(whoami)
USER_ID=$(id -u)

echo "export PATH=\$PATH:/home/$USER_NAME/bin" >> ~/.bashrc
echo "export DOCKER_HOST=unix:///run/user/$USER_ID/docker.sock" >> ~/.bashrc
source ~/.bashrc

# Set up Docker as a systemd user service

# Create the systemd service directory and file
mkdir -p ~/.config/systemd/user/
cat <<EOL > ~/.config/systemd/user/docker-rootless.service
[Unit]
Description=Docker Rootless
After=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=5s
ExecStart=/home/%u/bin/dockerd-rootless.sh

[Install]
WantedBy=default.target
EOL

# Reload systemd user instance, enable and start the service
systemctl --user daemon-reload
systemctl --user enable docker-rootless
systemctl --user start docker-rootless

# Ensure user-level systemd services start at boot
sudo loginctl enable-linger $(whoami)

echo "Docker in rootless mode has been installed and set to start on boot."
