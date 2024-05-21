SHELL := /bin/bash

.PHONY: sync-teams self-hosted-runner setup-runner install-agent centos ubuntu help


sync-teams:
ifeq ($(filter install,$(MAKECMDGOALS)),install)
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "Python 3 is required but it's not installed. Please install Python 3 (or ensure 'python3' command is available) and try again." >&2; \
		exit 1; \
	fi
	@if [ ! -d "venv-jit" ]; then \
		python3 -m venv venv-jit; \
	fi
	. venv-jit/bin/activate && pip install -r requirements.txt
endif
ifeq ($(filter configure,$(MAKECMDGOALS)),configure)
	@read -p "Enter GitHub organization name: " org_name; \
	read -p "Enter JIT API client ID: " client_id; \
	read -p "Enter JIT API client secret: " client_secret; \
	read -p "Enter GitHub Personal token (PAT): " github_token; \
	read -p "Enter comma separated topic wildcards to exclude the creation of teams(example: *dev*, *test*): " topics_to_exclude; \
	echo "ORGANIZATION_NAME=$$org_name" > .env; \
	echo "JIT_CLIENT_ID=$$client_id" >> .env; \
	echo "JIT_CLIENT_SECRET=$$client_secret" >> .env; \
	echo "GITHUB_API_TOKEN=$$github_token" >> .env; \
	echo "TEAM_WILDCARD_TO_EXCLUDE=$$topics_to_exclude" >> .env
endif
ifeq ($(filter run,$(MAKECMDGOALS)),run)
	. venv-jit/bin/activate && \
	export PYTHONPATH=$(CURDIR) && \
	python3 src/scripts/sync_teams/sync_teams.py teams.json
endif

install:
	@echo installation complete
configure:
	@echo configuration complete
run:
	@echo run complete


SELF_HOSTED_DOCKER_AMAZON_SCRIPT := src/scripts/self-hosted-runners/setup-rootless-docker-amazon.sh
SELF_HOSTED_DOCKER_UBUNTU_SCRIPT := src/scripts/self-hosted-runners/setup-rootless-docker-ubuntu.sh
SELF_HOSTED_RUNNER_SCRIPT := src/scripts/self-hosted-runners/install-github-runner-agent.sh


self-hosted-runner: check-root setup-runner install-agent

check-root:
	@if [ "$$UID" -eq 0 ]; then \
        echo "Error: This script should not be run as root."; \
        exit 1; \
    fi

setup-runner:
ifeq ($(filter amazon,$(MAKECMDGOALS)),amazon)
	sudo yum install -y jq
	chmod +x $(SELF_HOSTED_DOCKER_AMAZON_SCRIPT)
	./$(SELF_HOSTED_DOCKER_AMAZON_SCRIPT)
else ifeq ($(filter ubuntu,$(MAKECMDGOALS)),ubuntu)
	chmod +x $(SELF_HOSTED_DOCKER_UBUNTU_SCRIPT)
	./$(SELF_HOSTED_DOCKER_UBUNTU_SCRIPT)
endif

install-agent:
	chmod +x $(SELF_HOSTED_RUNNER_SCRIPT)
	./$(SELF_HOSTED_RUNNER_SCRIPT) $(runner_token) $(github_org)

amazon:
	@echo installed on amazon

ubuntu:
	@echo installed on ubuntu

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo " install        Install dependencies"
	@echo " configure      Configure environment variables"
	@echo " create-teams   Create teams based on input file"
	@echo " self-hosted-runner amazon runner_token=<runner-token> github_org=<github-organization> Set up self-hosted runner on Amazon Linux"
	@echo " self-hosted-runner ubuntu runner_token=<runner-token> github_org=<github-organization> Set up self-hosted runner on Ubuntu"
	@echo " install-agent  Install GitHub runner agent"
	@echo " help           Show this help message"
