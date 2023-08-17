import json
import os
from typing import List

import requests
from dotenv import load_dotenv
from github import Github
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

ORGANIZATION_NAME = os.getenv("ORGANIZATION_NAME")
FRONTEGG_AUTH_URL = os.getenv("FRONTEGG_AUTH_URL", "https://jit.frontegg.com/identity/resources/auth/v1/api-token")
JIT_API_ENDPOINT = os.getenv("JIT_API_ENDPOINT", "https://api.jit.io")
GITHUB_TOKEN = os.getenv("GITHUB_API_TOKEN")
JIT_CLIENT_SECRET = os.getenv("JIT_CLIENT_SECRET")
JIT_CLIENT_ID = os.getenv("JIT_CLIENT_ID")


class Repository(BaseModel):
    name: str
    topics: List[str]


def get_teams():
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

            # Create a Repository instance with repository details
            repo_details = Repository(name=repo_name, topics=topics)

            # Add repository details to the list
            repositories.append(repo_details)

        return repositories
    except Exception as e:
        print(f"Failed to retrieve teams: {str(e)}")
        return None


def list_assets(token):
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

            return assets
        else:
            print(f"Failed to retrieve assets. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Failed to retrieve assets: {str(e)}")
        return None


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


def main():
    token = get_jwt_token()
    if not token:
        print("Failed to retrieve JWT token. Exiting...")
        exit(-1)

    # Call the get_teams function
    teams = get_teams()
    if not teams:
        print("Failed to retrieve Teams. Exiting...")
        exit(-1)

    # Convert the list to JSON format
    json_data = json.dumps([t.model_dump() for t in teams], indent=2)

    # Print the JSON data
    print(json_data)

    # Call the list_assets function
    assets = list_assets(token)
    if not assets:
        print("Failed to retrieve assets. Exiting...")
        exit(-1)

    # Print the assets
    print(assets)


if __name__ == '__main__':
    main()
