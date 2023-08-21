import argparse
import json
import os
from typing import List, Optional

import requests
from dotenv import load_dotenv
from github import Github
from pydantic import BaseModel, ValidationError

# Load environment variables from .env file
load_dotenv()

ORGANIZATION_NAME = os.getenv("ORGANIZATION_NAME")
FRONTEGG_AUTH_URL = os.getenv("FRONTEGG_AUTH_URL", "https://jit.frontegg.com/identity/resources/auth/v1/api-token")
JIT_API_ENDPOINT = os.getenv("JIT_API_ENDPOINT", "https://api.jit.io")
GITHUB_TOKEN = os.getenv("GITHUB_API_TOKEN")
JIT_CLIENT_SECRET = os.getenv("JIT_CLIENT_SECRET")
JIT_CLIENT_ID = os.getenv("JIT_CLIENT_ID")
MANUAL_TEAM_SOURCE = "manual"
REPO = 'repo'


class RepositoryDetails(BaseModel):
    name: str
    topics: List[str]


class BaseTeam(BaseModel):
    tenant_id: str
    id: str
    created_at: str
    modified_at: str
    name: str
    description: Optional[str]
    parent_team_id: Optional[str]
    children_team_ids: List[str] = []
    score: int = 0
    source: str = MANUAL_TEAM_SOURCE


class Asset(BaseModel):
    asset_id: str
    tenant_id: str
    asset_type: str
    vendor: str
    owner: str
    asset_name: str
    is_active: bool
    is_covered: bool = True
    is_archived: Optional[bool] = False
    created_at: str
    modified_at: str
    environment: Optional[str]
    is_branch_protected_by_jit: Optional[bool]


def get_repos_from_github():
    try:
        # Create a GitHub instance using the token
        github = Github(GITHUB_TOKEN)

        # Get the organization
        organization = github.get_organization(ORGANIZATION_NAME)

        # List to store repository details
        repositories = []

        # Iterate over repositories in the organization
        for repo in organization.get_repos():
            # Get the repository name
            repo_name = repo.name

            # Get the repository topics
            topics = repo.get_topics()
            if not topics:
                continue
            # Create a Repository instance with repository details
            repo_details = RepositoryDetails(name=repo_name, topics=topics)

            # Add repository details to the list
            repositories.append(repo_details)

        return repositories
    except Exception as e:
        print(f"Failed to retrieve teams: {str(e)}")
        return None


def list_assets(token) -> List[Asset]:
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
            print(f"Failed to retrieve assets. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Failed to retrieve assets: {str(e)}")
        return []


def get_jwt_token():
    payload = {
        "clientId": JIT_CLIENT_ID,
        "secret": JIT_CLIENT_SECRET
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(FRONTEGG_AUTH_URL, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json().get('accessToken')
    else:
        print(f"Failed to retrieve JWT token. Status code: {response.status_code}")
        return None


def get_existing_teams(token) -> List[BaseTeam]:
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
                    print(f"Failed to retrieve teams. Status code: {response.status_code}, {response.text}")
                    return []

            return [BaseTeam(**team) for team in existing_teams]
        else:
            print(f"Failed to retrieve teams. Status code: {response.status_code}, {response.text}")
            return []
    except Exception as e:
        print(f"Failed to retrieve teams: {str(e)}")
        return []


def get_teams_to_create(topic_names, existing_team_names):
    return list(set(topic_names) - set(existing_team_names))


def get_teams_to_delete(topic_names, existing_team_names):
    return list(set(existing_team_names) - set(topic_names))


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Retrieve teams and assets")

    # Add the --input argument
    parser.add_argument("--input", help="Path to a JSON file")

    # Parse the command line arguments
    args = parser.parse_args()

    token = get_jwt_token()
    if not token:
        print("Failed to retrieve JWT token. Exiting...")
        return

    # Check if the --input argument is provided
    if args.input:
        # Check if the file exists and is a JSON file
        if not os.path.isfile(args.input):
            print("Error: File does not exist.")
            return
        if not args.input.endswith(".json"):
            print("Error: File is not a JSON file.")
            return

        # Read the JSON file
        with open(args.input, "r") as file:
            json_data = file.read()

        # Parse the JSON data
        try:
            repos = [RepositoryDetails(**team) for team in json.loads(json_data)]
        except ValidationError as e:
            print(f"Failed to validate input file: {e}")
            return
    else:
        # Call the get_teams function
        repos = get_repos_from_github()
        if not repos:
            print("Failed to retrieve topics. Exiting...")
            return

    topic_names = []
    for repo in repos:
        topic_names.extend(repo.topics)

    existing_teams: List[BaseTeam] = get_existing_teams(token)
    existing_team_names = [team.name for team in existing_teams]

    teams_to_create = get_teams_to_create(topic_names, existing_team_names)
    teams_to_delete = get_teams_to_delete(topic_names, existing_team_names)



    assets: List[Asset] = list_assets(token)
    if not assets:
        print("Failed to retrieve assets. Exiting...")
        return

    # Print the assets
    print(assets)


if __name__ == '__main__':
    main()
