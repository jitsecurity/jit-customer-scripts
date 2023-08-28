#!/bin/bash

# Exit on error
set -e

# Check if script is run as root
if [ "$EUID" -eq 0 ]; then
    echo "Please run this script as a non-root user."
    exit 1
fi

# Install required packages only if they aren't already installed

# Check for shadow-utils
if ! rpm -q shadow-utils &> /dev/null; then
    echo "Installing shadow-utils..."
    sudo yum install -y shadow-utils
fi

# Check for curl or curl-minimal
if ! rpm -q curl &> /dev/null && ! rpm -q curl-minimal &> /dev/null; then
    echo "Installing curl..."
    sudo yum install -y curl
fi

# Check for iptables
if ! rpm -q iptables &> /dev/null; then
    echo "Installing iptables..."
    sudo yum install -y iptables
fi

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

sudo yum install libicu -y
echo "Installed libicu Dotnet for the github agent"