install:
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "Python 3 is required but it's not installed. Please install Python 3 and try again." >&2; \
		exit 1; \
	fi
	@if [ ! -d "venv-jit" ]; then \
		python3 -m venv venv-jit; \
	fi
	source venv-jit/bin/activate && pip install -r requirements.txt

configure:
	@read -p "Enter GitHub organization name: " org_name; \
	read -p "Enter JIT API client ID: " client_id; \
	read -p "Enter JIT API client secret: " client_secret; \
	read -p "Enter GitHub Personal token (PAT): " github_token; \
	echo "ORGANIZATION_NAME=$$org_name" > .env; \
	echo "JIT_CLIENT_ID=$$client_id" >> .env; \
	echo "JIT_CLIENT_SECRET=$$client_secret" >> .env; \
	echo "GITHUB_API_TOKEN=$$github_token" >> .env

create-teams:
	source venv-jit/bin/activate && export PYTHONPATH=$(CURDIR) && python src/utils/github_topic_to_json_file.py && python src/operation_create_teams.py --input repos.json

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo " install        Install dependencies"
	@echo " configure      Configure environment variables"
	@echo " create-teams   Create teams based on input file"
	@echo " help           Show this help message"
