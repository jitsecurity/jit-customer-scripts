import argparse
from ast import Or
import json
import os
import sys
from typing import List, Dict

from dotenv import load_dotenv
from loguru import logger
from pydantic import ValidationError
from src.shared.clients.jit import get_existing_teams, create_teams, list_assets, add_teams_to_asset, delete_teams, \
    get_jit_jwt_token, set_manual_team_members
from src.shared.consts import MAX_MEMBERS_PER_TEAM
from src.shared.diff_tools import get_different_items_in_lists
from src.shared.models import Asset, TeamAttributes, Organization, TeamStructure, ResourceType

# Load environment variables from .env file.
load_dotenv()

logger.remove()  # Remove default handler
logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <2}</level> | {message}"
logger.add(sys.stderr, format=logger_format)


def parse_input_file() -> Organization:
    """
    Parse the input JSON file and return an Organization object.

    Returns:
        Organization: The parsed organization object.
    """
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Retrieve teams and assets")

    # Add the file argument
    parser.add_argument("file", help="Path to a JSON file")

    # Parse the command line arguments
    args = parser.parse_args()

    # Check if the file exists and is a JSON file
    if not os.path.isfile(args.file):
        logger.error("Error: File does not exist.")
        sys.exit(1)
    if not args.file.endswith(".json"):
        logger.error("Error: File is not a JSON file.")
        sys.exit(1)

    # Read the JSON file
    with open(args.file, "r") as file:
        json_data = file.read()

    # Parse the JSON data
    try:
        data = json.loads(json_data)
        return Organization(teams=[TeamStructure(**team) for team in data["teams"]])
    except (ValidationError, KeyError) as e:
        logger.error(f"Failed to validate input file: {e}")
        sys.exit(1)


def update_assets(token, assets: List[Asset], organization: Organization,
                  existing_teams: List[TeamAttributes]):
    """
    Update the assets with the teams specified in the organization.

    Args:
        token (str): The JWT token.
        organization (Organization): The organization object.

    Returns:
        None
    """
    logger.info("Updating assets.")

    asset_to_team_map = get_teams_for_assets(organization)
    existing_teams: List[str] = [t.name for t in existing_teams]
    for asset in assets:
        teams_to_update = asset_to_team_map.get(asset.asset_name, [])
        if teams_to_update:
            excluded_teams = get_different_items_in_lists(
                teams_to_update, existing_teams)
            if excluded_teams:
                logger.info(
                    f"Excluding topic(s) {excluded_teams} for asset '{asset.asset_name}'")
                teams_to_update = list(
                    set(teams_to_update) - set(excluded_teams))
            logger.info(
                f"Syncing team(s) {teams_to_update} to asset '{asset.asset_name}'")
            add_teams_to_asset(token, asset, teams_to_update)
        else:
            asset_has_teams_tag = asset.tags and "team" in [
                t.name for t in asset.tags]
            if asset_has_teams_tag:
                logger.info(
                    f"Removing all teams from asset '{asset.asset_name}'")
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


def get_desired_teams(assets: List[Asset], organization: Organization) -> List[str]:
    """
    Get the desired teams based on the assets and organization.
    Also filter out teams that match the TEAM_WILDCARD_TO_EXCLUDE environment variable.

    Args:
        assets (List[Asset]): The list of assets.
        organization (Organization): The organization object.

    Returns:
        List[str]: The names of the desired teams.
    """
    desired_teams = []
    for team in organization.teams:
        team_resources = []
        for resource in team.resources:
            if resource.type == ResourceType.GithubRepo and resource.name in [asset.asset_name for asset in assets]:
                team_resources.append(resource.name)
        if team_resources:
            desired_teams.append(team.name)
        else:
            logger.info(
                f'Skipping team {team.name} as it has no active resources in the organization.')

    wildcards_to_exclude = os.getenv("TEAM_WILDCARD_TO_EXCLUDE", "").split(",")
    final_desired_teams = []
    for team_name in desired_teams:
        exclude_team = False
        for wildcard in wildcards_to_exclude:
            wildcard = wildcard.strip().strip("*")
            if wildcard and wildcard in team_name:
                exclude_team = True
                break
        if not exclude_team:
            final_desired_teams.append(team_name)

    return final_desired_teams


def process_teams(token, organization, assets: List[Asset]) -> List[str]:
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

    desired_teams = get_desired_teams(assets, organization)
    existing_teams: List[TeamAttributes] = get_existing_teams(token)
    existing_team_names = [team.name for team in existing_teams]
    teams_to_create = get_teams_to_create(desired_teams, existing_team_names)
    teams_to_delete = get_teams_to_delete(desired_teams, existing_team_names)
    if teams_to_create:
        logger.info(
            f"Creating {len(teams_to_create)} team(s): {teams_to_create}")
        create_teams(token, teams_to_create)
    return teams_to_delete


def process_members(token: str, organization: Organization, existing_teams: List[TeamAttributes],
                    desired_teams: List[str]) -> None:
    logger.info("Processing team members.")
    for team_structure in organization.teams:
        try:
            team_name = team_structure.name
            team_members = team_structure.members

            # Find the corresponding existing team
            existing_team = next(
                (team for team in existing_teams if team.name == team_name), None)
            if existing_team and team_name in desired_teams:
                team_id = existing_team.id
                if len(team_members) > MAX_MEMBERS_PER_TEAM:
                    logger.warning(f"Team '{team_name}' has more than {MAX_MEMBERS_PER_TEAM} members. "
                                   f"Only the first {MAX_MEMBERS_PER_TEAM} members will be set.")
                    team_members = team_members[:MAX_MEMBERS_PER_TEAM]
                set_manual_team_members(
                    token, team_id, team_members, team_name)
            else:
                logger.warning(
                    f"Team '{team_name}' not found in existing teams. Skipping member processing.")
        except Exception as e:
            logger.error(
                f"Failed to process members for team '{team_name}': {str(e)}")


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
            if resource.type == ResourceType.GithubRepo:
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

    assets: List[Asset] = list_assets(jit_token)

    teams_to_delete = process_teams(jit_token, organization, assets)
    existing_teams: List[TeamAttributes] = get_existing_teams(jit_token)
    desired_teams = get_desired_teams(assets, organization)
    process_members(jit_token, organization, existing_teams, desired_teams)
    update_assets(jit_token, assets, organization, existing_teams)

    if teams_to_delete:
        logger.info(
            f"Checking which team(s) to delete from: {teams_to_delete}")
        delete_teams(jit_token, teams_to_delete)
    logger.info("Successfully completed teams sync.")


if __name__ == '__main__':
    main()
