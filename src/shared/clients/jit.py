import os
from typing import List
from typing import Optional

import requests
from loguru import logger
from src.shared.env_tools import get_jit_endpoint_base_url
from src.shared.models import Asset, TeamAttributes


def get_jit_jwt_token() -> Optional[str]:
    payload = {
        "clientId": os.getenv('JIT_CLIENT_ID'),
        "secret": os.getenv('JIT_CLIENT_SECRET')
    }

    response = requests.post(f"{get_jit_endpoint_base_url()}/authentication/login",
                             json=payload)

    if response.status_code == 200:
        return response.json().get('accessToken')
    else:
        logger.error(f"Failed to retrieve JWT token. Status code: {response.status_code}")
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
            logger.error(f"Failed to retrieve assets. Status code: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Failed to retrieve assets: {str(e)}")
        return []


def get_existing_teams(token: str) -> List[TeamAttributes]:
    def _handle_resoponse(response, existing_teams):
        response = response.json()
        data = response['data']
        existing_teams.extend(data)
        after = response['metadata']['after']
        return after

    try:
        # Make a GET request to the asset API
        url = f"{get_jit_endpoint_base_url()}/teams?limit=100"

        headers = get_request_headers(token)
        response = requests.get(url, headers=headers)
        existing_teams = []
        # Check if the request was successful
        if response.status_code == 200:
            after = _handle_resoponse(response, existing_teams)
            while after:
                response = requests.get(f"{url}&after={after}", headers=headers)
                if response.status_code == 200:
                    after = _handle_resoponse(response, existing_teams)
                else:
                    logger.error(f"Failed to retrieve teams. Status code: {response.status_code}, {response.text}")
                    return []

            logger.info("Retrieved existing teams successfully.")
            return [TeamAttributes(**team) for team in existing_teams]
        else:
            logger.error(f"Failed to retrieve teams. Status code: {response.status_code}, {response.text}")
            return []
    except Exception as e:
        logger.error(f"Failed to retrieve teams: {str(e)}")
        return []


def delete_teams(token, team_names):
    existing_teams: List[TeamAttributes] = get_existing_teams(token)

    for team_name in team_names:
        team_id = None
        for team in existing_teams:
            if team.name == team_name:
                team_id = team.id
                break

        if team_id:
            url = f"{get_jit_endpoint_base_url()}/teams/{team_id}"
            headers = {"Authorization": f"Bearer {token}"}

            response = requests.delete(url, headers=headers)

            if response.status_code == 204:
                logger.info(f"Team '{team_name}' deleted successfully.")
            else:
                logger.error(
                    f"Failed to delete team '{team_name}'. Status code: {response.status_code}, {response.text}")
        else:
            logger.warning(f"Team '{team_name}' not found.")


def create_teams(token, teams_to_create):
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
            else:
                logger.error(
                    f"Failed to create team '{team_name}'. Status code: {response.status_code}, {response.text}")
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
            logger.info(f"Team(s) synced to asset '{asset.asset_name}' successfully.")
        else:
            logger.error(f"Failed to add teams to asset '{asset.asset_id}'. Status code: "
                         f"{response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"Failed to add teams to asset: {str(e)}")
