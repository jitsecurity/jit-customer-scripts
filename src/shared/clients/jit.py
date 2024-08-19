import os
from typing import List
from typing import Optional

import requests
from loguru import logger
from src.shared.consts import MANUAL_TEAM_SOURCE, MAX_RETRIES
from src.shared.env_tools import get_jit_endpoint_base_url
from src.shared.models import Asset, TeamAttributes


def get_jit_jwt_token() -> Optional[str]:
    payload = {
        "clientId": os.getenv('JIT_CLIENT_ID'),
        "secret": os.getenv('JIT_CLIENT_SECRET')
    }
    jit_endpoint = get_jit_endpoint_base_url()
    logger.info(f"Using {jit_endpoint} endpoint.")
    response = requests.post(f"{jit_endpoint}/authentication/login",
                             json=payload)

    if response.status_code == 200:
        return response.json().get('accessToken')
    else:
        logger.error(
            f"Failed to retrieve JWT token. Status code: {response.status_code}")
        return None


def list_assets(token: str) -> List[Asset]:
    try:
        # Make a GET request to the asset API
        url = f"{get_jit_endpoint_base_url()}/asset"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response JSON
            assets = response.json()

            logger.info("Retrieved assets successfully.")
            return [Asset(**asset) for asset in assets]
        else:
            logger.error(
                f"Failed to retrieve assets. Status code: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Failed to retrieve assets: {str(e)}")
        return []


def get_existing_teams(token: str) -> List[TeamAttributes]:
    headers = {
        'authorization': f'Bearer {token}',
    }

    params = {
        'limit': '50',
        'sort_by': 'score',
        'sort_order': 'desc',
        'include_members': 'true',
    }

    all_teams = []
    while True:
        response = requests.get(
            'https://api.rocket.jitdev.io/teams', params=params, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            teams = response_data.get('data', [])
            all_teams.extend(teams)
            after = response_data.get('metadata', {}).get('after')

            if not after:
                break  # Exit loop if there's no 'after' for the next page

            # Prepare params for the next request with pagination
            params['page'] = after
        else:
            print(
                f"Failed to retrieve teams. Status code: {response.status_code}, {response.text}")
            break

    return [TeamAttributes(**team) for team in all_teams]


def delete_teams(token, team_names):
    existing_teams: List[TeamAttributes] = get_existing_teams(token)

    for team_name in team_names:
        team_id = None
        selected_team = None
        for team in existing_teams:
            if team.name == team_name:
                team_id = team.id
                selected_team = team
                break

        # We only delete teams that are manually created
        if team_id:
            if selected_team and selected_team.source == MANUAL_TEAM_SOURCE:
                url = f"{get_jit_endpoint_base_url()}/teams/{team_id}"
                headers = {"Authorization": f"Bearer {token}"}

                response = requests.delete(url, headers=headers)

                if response.status_code == 204:
                    logger.info(f"Team '{team_name}' deleted successfully.")
                else:
                    logger.error(
                        f"Failed to delete team '{team_name}'. Status code: {response.status_code}, {response.text}")
            else:
                logger.info(
                    f"Team '{team_name}' is not manually created. Skipping deletion.")
        else:
            logger.warning(f"Team '{team_name}' not found.")


def create_teams(token, teams_to_create):
    created_teams: List[TeamAttributes] = []
    try:
        url = f"{get_jit_endpoint_base_url()}/teams/"
        headers = get_request_headers(token)
        for team_name in teams_to_create:
            payload = {
                "name": team_name
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                logger.info(f"Team '{team_name}' created successfully.")
                created_teams.append(TeamAttributes(**response.json()))
            else:
                logger.error(
                    f"Failed to create team '{team_name}'. Status code: {response.status_code}, {response.text}")
        return created_teams
    except Exception as e:
        logger.error(f"Failed to create teams: {str(e)}")


def get_request_headers(token):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    return headers


def add_teams_to_asset(token, asset: Asset, teams: List[str]):
    try:
        url = f"{get_jit_endpoint_base_url()}/asset/asset/{asset.asset_id}"
        headers = get_request_headers(token)
        payload = {
            "teams": teams
        }
        response = requests.patch(url, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info(
                f"Team(s) synced to asset '{asset.asset_name}' successfully.")
        else:
            logger.error(f"Failed to add teams to asset '{asset.asset_id}'. Status code: "
                         f"{response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"Failed to add teams to asset: {str(e)}")


def _perform_set_manual_team_members(token: str, team_id: str,
                                     members: List[str], team_name: str,
                                     verify_github_membership: bool) -> Optional[List[str]]:
    try:
        url = f"{get_jit_endpoint_base_url()}/teams/{team_id}/members"
        headers = get_request_headers(token)
        payload = {
            "members": members,
            "verify_github_membership": verify_github_membership
        }
        response = requests.put(url, json=payload, headers=headers)
        if response.status_code == 200:
            failed_members = response.json().get("failed_members", [])
            if failed_members:
                logger.warning(
                    f"Failed to set some members for team '{team_name}' with ID '{team_id}': {failed_members}")
            else:
                logger.info(
                    f"Members set for team '{team_name}' with ID '{team_id}' successfully.")
            return failed_members
        else:
            logger.error(f"Failed to set members for team '{team_name}' with ID '{team_id}'. Status code: "
                         f"{response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(
            f"Failed to set members for team with ID '{team_id}': {str(e)}")
        return None


def set_manual_team_members(token: str, team_id: str, members: List[str],
                            team_name: str, verify_github_membership: bool) -> None:
    retry_count = 0
    failed_members = _perform_set_manual_team_members(
        token, team_id, members, team_name, verify_github_membership)
    while retry_count <= MAX_RETRIES and failed_members:
        failed_members = _perform_set_manual_team_members(
            token, team_id, members, team_name, verify_github_membership)
        # We send all members, not just the failed ones. Otherwise it would set the list
        # to only the failed members
        retry_count += 1

    if failed_members:
        logger.error(f"Failed to set some members for team with ID '{team_id}' after {MAX_RETRIES} retries: "
                     f"{failed_members}")
