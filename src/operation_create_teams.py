import argparse
import json
import os
import sys
from typing import List

from dotenv import load_dotenv
from loguru import logger
from pydantic import ValidationError

from src.shared.clients.frontegg import get_jwt_token
from src.shared.clients.github import get_teams_from_github_topics
from src.shared.clients.jit import get_existing_teams, create_teams, list_assets, add_teams_to_asset
from src.shared.diff_tools import get_teams_to_create, get_teams_to_delete
from src.shared.models import Asset, BaseTeam, Organization, TeamTemplate, AssetToTeamMap

# Load environment variables from .env file. make sure it's before you import modules.
load_dotenv()


def parse_input_file() -> Organization:
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Retrieve teams and assets")

    # Add the --input argument
    parser.add_argument("--input", help="Path to a JSON file")

    # Parse the command line arguments
    args = parser.parse_args()

    # Check if the --input argument is provided
    if args.input:
        # Check if the file exists and is a JSON file
        if not os.path.isfile(args.input):
            logger.error("Error: File does not exist.")
            sys.exit(1)
        if not args.input.endswith(".json"):
            logger.error("Error: File is not a JSON file.")
            sys.exit(1)

        # Read the JSON file
        with open(args.input, "r") as file:
            json_data = file.read()

        # Parse the JSON data
        try:
            data = json.loads(json_data)
            return Organization(teams=[TeamTemplate(**team) for team in data["teams"]])
        except ValidationError as e:
            logger.error(f"Failed to validate input file: {e}")
            sys.exit(1)
    else:
        logger.error("No input file provided.")
        sys.exit(1)


def update_assets(token, organization):
    assets: List[Asset] = list_assets(token)
    asset_to_team_map = get_teams_for_assets(organization)
    for asset in assets:
        for repo in organization:
            if asset.asset_name == repo.name:
                add_teams_to_asset(token, asset, repo.topics)


def process_teams(token, organization):
    desired_teams = [t.name for t in organization.teams]
    existing_teams: List[BaseTeam] = get_existing_teams(token)
    existing_team_names = [team.name for team in existing_teams]
    teams_to_create = get_teams_to_create(desired_teams, existing_team_names)
    teams_to_delete = get_teams_to_delete(desired_teams, existing_team_names)
    if teams_to_create:
        create_teams(token, teams_to_create)
    return teams_to_delete


def get_teams_for_assets(organization: Organization) -> List[AssetToTeamMap]:
    asset_to_team_map = []
    for team in organization.teams:
        for resource in team.resources:
            if resource.type == "github_repo":
                asset_to_team_map.append(AssetToTeamMap(asset_name=resource.name, teams=[team.name]))
    return asset_to_team_map


def main():
    token = get_jwt_token()
    if not token:
        logger.error("Failed to retrieve JWT token. Exiting...")
        return

    organization: Organization = parse_input_file()
    if not organization:
        return

    teams_to_delete = process_teams(token, organization)



    if teams_to_delete:
        print(teams_to_delete)


    update_assets(token, organization)


if __name__ == '__main__':
    logger.add("app.log", rotation="500 MB", level="INFO")
    main()
