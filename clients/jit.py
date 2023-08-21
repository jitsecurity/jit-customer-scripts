import os
from typing import List

import requests
from dotenv import load_dotenv
from loguru import logger

from consts import JIT_DEFAULT_API_ENDPOINT
from models import Asset, BaseTeam

# Load environment variables from .env file. make sure it's before you import modules.
load_dotenv(".env")
JIT_API_ENDPOINT = os.getenv("JIT_API_ENDPOINT", JIT_DEFAULT_API_ENDPOINT)


def list_assets(token: str) -> List[Asset]:
    try:
        # Make a GET request to the asset API
        url = f"{JIT_API_ENDPOINT}/asset"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response JSON
            assets = response.json()

            return [Asset(**asset) for asset in assets]
        else:
            logger.error(f"Failed to retrieve assets. Status code: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Failed to retrieve assets: {str(e)}")
        return []


def get_existing_teams(token: str) -> List[BaseTeam]:
    def _handle_resoponse(response, existing_teams):
        response = response.json()
        data = response['data']
        existing_teams.extend(data)
        after = response['metadata']['after']
        return after

    try:
        # Make a GET request to the asset API
        url = f"{JIT_API_ENDPOINT}/teams?limit=100"

        headers = {
            "Authorization": f"Bearer {token}"
        }
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

            return [BaseTeam(**team) for team in existing_teams]
        else:
            logger.error(f"Failed to retrieve teams. Status code: {response.status_code}, {response.text}")
            return []
    except Exception as e:
        logger.error(f"Failed to retrieve teams: {str(e)}")
        return []


def create_teams(token, teams_to_create):
    try:
        url = f"{JIT_API_ENDPOINT}/teams/"
        headers = {
            "Authorization": f"Bearer {token}",
        }
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