import argparse
import json
import os
from typing import List

from dotenv import load_dotenv

# Load environment variables from .env file. make sure it's before you import modules.
load_dotenv()
from loguru import logger
from pydantic import ValidationError

from clients.frontegg import get_jwt_token
from clients.github import get_repos_from_github
from clients.jit import get_existing_teams, create_teams, list_assets
from models import RepositoryDetails, Asset, BaseTeam
from utils import get_teams_to_create, get_teams_to_delete


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Retrieve teams and assets")

    # Add the --input argument
    parser.add_argument("--input", help="Path to a JSON file")

    # Parse the command line arguments
    args = parser.parse_args()

    token = get_jwt_token()
    if not token:
        logger.error("Failed to retrieve JWT token. Exiting...")
        return

    # Check if the --input argument is provided
    if args.input:
        # Check if the file exists and is a JSON file
        if not os.path.isfile(args.input):
            logger.error("Error: File does not exist.")
            return
        if not args.input.endswith(".json"):
            logger.error("Error: File is not a JSON file.")
            return

        # Read the JSON file
        with open(args.input, "r") as file:
            json_data = file.read()

        # Parse the JSON data
        try:
            repos = [RepositoryDetails(**team) for team in json.loads(json_data)]
        except ValidationError as e:
            logger.error(f"Failed to validate input file: {e}")
            return
    else:
        # Call the get_teams function
        repos = get_repos_from_github()
        if not repos:
            logger.error("Failed to retrieve topics. Exiting...")
            return

    topic_names = []
    for repo in repos:
        topic_names.extend(repo.topics)

    existing_teams: List[BaseTeam] = get_existing_teams(token)
    existing_team_names = [team.name for team in existing_teams]

    teams_to_create = get_teams_to_create(topic_names, existing_team_names)
    teams_to_delete = get_teams_to_delete(topic_names, existing_team_names)

    create_teams(token, teams_to_create)

    assets: List[Asset] = list_assets(token)
    if not assets:
        logger.error("Failed to retrieve assets. Exiting...")
        return

    # Print the assets
    logger.info(assets)


if __name__ == '__main__':
    logger.add("app.log", rotation="500 MB", level="INFO")
    main()
