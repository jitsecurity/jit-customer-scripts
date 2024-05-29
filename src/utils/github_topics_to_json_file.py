import sys
import os

from dotenv import load_dotenv
from loguru import logger

from src.shared.clients.github import get_teams_from_github_topics

# Load environment variables from .env file.

TEAMS_JSON_FILE = os.getenv("TEAMS_JSON_FILE", "../teams.json")

load_dotenv()
logger.remove()  # Remove default handler
logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <2}</level> | {message}"
logger.add(sys.stderr, format=logger_format)
if __name__ == '__main__':
    teams = get_teams_from_github_topics()
    with open(TEAMS_JSON_FILE, "w") as file:
        file.write(teams.model_dump_json(indent=2))
