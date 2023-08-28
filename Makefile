SHELL := /bin/bash

install:
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "Python 3 is required but it's not installed. Please install Python 3 (or ensure 'python3' command is available) and try again." >&2; \
		exit 1; \
	fi
	@if [ ! -d "venv-jit" ]; then \
		python3 -m venv venv-jit; \
	fi
	. venv-jit/bin/activate && pip install -r requirements.txt

configure:
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

create-teams:
	. venv-jit/bin/activate && \
	export PYTHONPATH=$(CURDIR) && \
	 python3 src/utils/github_topics_to_json_file.py && \
	  python3 src/scripts/create_teams.py teams.json

setup-self-hosted-runner-centos:
	sudo yum install -y jq && \
	chmod +x src/scripts/self-hosted-runners/setup-self-hosted-runner-centos.sh && \
	./src/scripts/self-hosted-runners/setup-self-hosted-runner-centos.sh && \
	chmod +x src/scripts/self-hosted-runners/install-github-runner-agent.sh && \
	./src/scripts/self-hosted-runners/install-github-runner-agent.sh $(token) $(github_organization)


help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo " install        Install dependencies"
	@echo " configure      Configure environment variables"
	@echo " create-teams   Create teams based on input file"
	@echo " help           Show this help message"
