import argparse
import json
import os
import sys
from typing import List, Dict

from dotenv import load_dotenv
from loguru import logger
from pydantic import ValidationError

from src.shared.clients.jit import get_existing_teams, create_teams, list_assets, add_teams_to_asset, delete_teams, \
    get_jit_jwt_token
from src.shared.diff_tools import get_different_items_in_lists
from src.shared.models import Asset, TeamObject, Organization, TeamTemplate

# Load environment variables from .env file.
load_dotenv()


def parse_input_file() -> Organization:
    """
    Parse the input JSON file and return an Organization object.

    Returns:
        Organization: The parsed organization object.
    """
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
    """
    Update the assets with the teams specified in the organization.

    Args:
        token (str): The JWT token.
        organization (Organization): The organization object.

    Returns:
        None
    """
    logger.info("Updating assets.")
    assets: List[Asset] = list_assets(token)
    asset_to_team_map = get_teams_for_assets(organization)
    for asset in assets:
        teams_to_update = asset_to_team_map.get(asset.asset_name, [])
        if teams_to_update:
            logger.info(f"Adding teams {teams_to_update} to asset {asset.asset_name}")
            add_teams_to_asset(token, asset, teams_to_update)


def get_teams_to_create(topic_names: List[str], existing_team_names: List[str]) -> List[str]:
    """
    Get the list of teams to create based on the desired teams and existing teams.

    Args:
        topic_names (List[str]): The desired team names.
        existing_team_names (List[str]): The existing team names.

    Returns:
        List[str]: The names of the teams to create.
    """
    return get_different_items_in_lists(topic_names, existing_team_names)


def get_teams_to_delete(topic_names: List[str], existing_team_names: List[str]) -> List[str]:
    """
    Get the list of teams to delete based on the desired teams and existing teams.

    Args:
        topic_names (List[str]): The desired team names.
        existing_team_names (List[str]): The existing team names.

    Returns:
        List[str]: The names of the teams to delete.
    """
    return get_different_items_in_lists(existing_team_names, topic_names)


def process_teams(token, organization):
    """
    Process the teams in the organization and create or delete teams as necessary.
    We will delete the teams at a later stage to avoid possible synchronization issues.

    Args:
        token (str): The JWT token.
        organization (Organization): The organization object.

    Returns:
        List[str]: The names of the teams to delete.
    """
    logger.info("Determining required changes in teams.")
    desired_teams = [t.name for t in organization.teams]
    existing_teams: List[TeamObject] = get_existing_teams(token)
    existing_team_names = [team.name for team in existing_teams]
    teams_to_create = get_teams_to_create(desired_teams, existing_team_names)
    teams_to_delete = get_teams_to_delete(desired_teams, existing_team_names)
    if teams_to_create:
        logger.info(f"Creating {len(teams_to_create)} teams: {teams_to_create}")
        create_teams(token, teams_to_create)
    return teams_to_delete


def get_teams_for_assets(organization: Organization) -> Dict[str, List[str]]:
    """
    Get the mapping of assets to teams from the organization.

    Args:
        organization (Organization): The organization object.

    Returns:
        Dict[str, List[str]]: The mapping of assets to teams.
    """
    asset_to_team_map = {}
    for team in organization.teams:
        for resource in team.resources:
            if resource.type == "github_repo":
                asset_name = resource.name
                if asset_name in asset_to_team_map:
                    asset_to_team_map[asset_name].append(team.name)
                else:
                    asset_to_team_map[asset_name] = [team.name]
    return asset_to_team_map


def main():
    logger.info("Starting the update process.")
    jit_token = get_jit_jwt_token()
    if not jit_token:
        logger.error("Failed to retrieve JWT token. Exiting...")
        return

    organization: Organization = parse_input_file()
    if not organization:
        logger.error("Failed to parse input file. Exiting...")
        return

    teams_to_delete = process_teams(jit_token, organization)

    update_assets(jit_token, organization)

    if teams_to_delete:
        logger.info(f"Deleting {len(teams_to_delete)} teams: {teams_to_delete}")
        delete_teams(jit_token, teams_to_delete)


if __name__ == '__main__':
    logger.add("app.log", rotation="5 MB", level="INFO")
    main()
