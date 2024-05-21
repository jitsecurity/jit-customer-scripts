import os
import json
from loguru import logger
from pydantic import ValidationError
from typing import List, Dict

from src.shared.models import Organization, MemberMapping

# Load environment variables from .env file.
members_mapping_file = os.getenv(
    'MEMBERS_MAPPING_FILE', '../members_mapping.json')


def load_json_file(file_path: str):
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json_file(file_path: str, data: Dict):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def update_teams_with_members(organization: Organization, members_mapping: List[MemberMapping]):
    members_dict = {
        mapping.team_name: mapping.members for mapping in members_mapping}
    for team in organization.teams:
        if team.name in members_dict:
            team.members = members_dict[team.name]
    return organization


def main():
    logger.info(os.listdir('..'))
    logger.info(f"Loading members mapping from {members_mapping_file}")
    members_mapping_data = load_json_file(members_mapping_file)
    members_mapping = [MemberMapping(team_name=team_name, members=members)
                       for team_name, members in members_mapping_data.items()]

    logger.info("Loading teams data from teams.json")
    teams_data = load_json_file('teams.json')
    organization = Organization(**teams_data)

    updated_organization = update_teams_with_members(
        organization, members_mapping)

    logger.info("Saving updated teams data to teams.json")
    save_json_file('teams.json', updated_organization.dict())
    logger.info("Successfully updated teams.json with members")


if __name__ == '__main__':
    try:
        main()
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
