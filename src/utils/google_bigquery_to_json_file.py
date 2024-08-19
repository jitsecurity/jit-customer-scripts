import sys

from dotenv import load_dotenv
from loguru import logger

from src.shared.clients.google import get_teams_from_bigquery_view

# Load environment variables from .env file.
load_dotenv()
logger.remove()  # Remove default handler
logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <2}</level> | {message}"
logger.add(sys.stderr, format=logger_format)


def generate_teams_json_file_from_bigquery():
    teams = get_teams_from_bigquery_view()
    with open("teams.json", "w") as file:
        file.write(teams.model_dump_json(indent=2))


if __name__ == '__main__':
    generate_teams_json_file_from_bigquery()
