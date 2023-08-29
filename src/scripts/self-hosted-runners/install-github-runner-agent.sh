#!/bin/bash

# Exit on error
set -e

# Assigning arguments to named variables for clarity
runner_token="$1"
github_organization="$2"
jit_repo_name="$3"

# Ensure both arguments are provided
if [ -z "$user_token" ] || [ -z "$github_organization" ];  || [ -z "$jit_repo_name" ]; then
    echo "Usage: $0 <user_token> <github_organization>"
    exit 1
fi

mkdir ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-x64-2.308.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.308.0/actions-runner-linux-x64-2.308.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.308.0.tar.gz
# Create the runner and start the configuration experience
./config.sh --url "https://github.com/$github_organization/$jit_repo_name" --token "runner_token"

sudo ./svc.sh install ec2-user
