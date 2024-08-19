<<<<<<< HEAD
from math import log
=======
>>>>>>> main
import os
import requests
import time
from github import Github, Auth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import sys

# Replace with your actual organization name
TOPIC = os.getenv('TOPIC_TO_UNCOVER', '')
ORGANIZATION = os.getenv('GITHUB_ORGANIZATION', '')

MAX_RETRIES = 5
RETRY_BACKOFF_FACTOR = 2


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)

    assets_deactivated = AssetesDeactivate(logger=logger)
    assets_deactivated.run(TOPIC, ORGANIZATION)


class AssetesDeactivate:
    def __init__(self, logger):
        self.logger = logger

    def run(self, topic, org):
        self.logger.info(
            f"Fetching repositories with the {topic} topic in org {org}...")
        if not org:
            self.logger.error(
                "GITHUB_ORGANIZATION environment variable is not set.")
            exit(1)
        if not topic:
            self.logger.error(
                "TOPIC_TO_UNCOVER environment variable is not set.")
            exit(1)
        relevant_repos = self.get_topic_repos(topic, org)
        auth_token = self.jit_authentication()

        # Check if token is valid for only 1 hour
        failed_repos = []
        for repo in relevant_repos:
            try:
                self.jit_deactivate_asset(repo, auth_token)
            except Exception as e:
                self.logger.error(
                    f"Failed to deactivate asset for repository: {repo.name}. Error message: {str(e)}")
                failed_repos.append(repo.name)
        if failed_repos:
            self.logger.warn(
                f"Failed to deactivate assets for the following repositories: {failed_repos}")

    def get_topic_repos(self, topic, org):
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token == "" or github_token is None:
            self.logger.error("GITHUB_TOKEN environment variable is not set.")
            exit(1)

        auth = Auth.Token(github_token)
        github_client = Github(auth=auth)

        repos = github_client.get_organization(org).get_repos()
        # Can take a while, 10-20 seconds

        filterd_repos = []
        for repo in repos:
            if topic in repo.topics:
                filterd_repos.append(repo)
        self.logger.info(
            f"Found {len(filterd_repos)} repositories with the {topic} topic in org {org}.")
        return filterd_repos

    def jit_authentication(self):
        """Authenticate with the JIT API and retrieve the access token."""
        auth_url = "https://api.jit.io/authentication/login"
        auth_payload = {
            "clientId": os.getenv('JIT_CLIENT_ID'),
            "secret": os.getenv('JIT_SECRET')
        }
        auth_headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        self.logger.info(
            f"Authenticating with JIT API using client ID: {auth_payload['clientId']}")
        response = self.send_request(
            url=auth_url, method="POST", headers=auth_headers, json=auth_payload)

        if response.status_code == 200:
            token = response.json().get('accessToken')
            self.logger.info("Authentication successful.")
            return token
        else:
            self.logger.error("Authentication failed. Exiting.")
            exit(1)

    def jit_deactivate_asset(self, repo, token):
        repo_name = repo.name
        self.logger.info(f"Processing repository: {repo_name}")

        asset_url = f"https://api.jit.io/asset/type/repo/vendor/github/owner/{repo.owner.login}/name/{repo_name}"
        asset_headers = {
            "accept": "application/json",
            "authorization": f"Bearer {token}"
        }

        self.logger.info(f"Fetching asset for repository: {repo_name}")
        asset_response = self.send_request(
            url=asset_url, headers=asset_headers)
        self.logger.info(
            f"Asset response status for {repo_name}: {asset_response.status_code}")

        if asset_response.status_code != 200:
            self.logger.error(
                f"Failed to fetch asset for repository {repo_name}!")
            return
        asset = asset_response.json()

        if asset.get('is_covered') is False:
            self.logger.info(
                f"Asset is already deactivated for repository: {repo_name}. Skipping...")
            return
        self.deactivate_asset(updated_asset=asset, token=token)
        self.logger.info(f"Asset deactivated for repository: {repo_name}")

    def deactivate_asset(self, updated_asset, token):
        update_url = f"https://api.jit.io/asset/asset/{updated_asset['asset_id']}"
        asset_headers = {
            "accept": "application/json",
            "authorization": f"Bearer {token}"
        }
        fields_to_update = {
            # "is_active": False,
            "is_covered": False
        }

        self.logger.info(
            f"Updating asset: {updated_asset['asset_id']} with data: {fields_to_update}")
        update_response = self.send_request(
            url=update_url, method="PATCH", headers=asset_headers, json=fields_to_update)
        self.logger.info(
            f"Update response status: {update_response.status_code}")

    def retry_request(func):
        """Decorator to retry a request in case of failure."""

        def wrapper(self, *args, **kwargs):
            retries = MAX_RETRIES
            backoff_factor = RETRY_BACKOFF_FACTOR
            response = None
            for attempt in range(retries):
                response = func(*args, **kwargs)
                if response.status_code == 200:
                    return response
                elif response.status_code == 401:
                    self.logger.warn(
                        "Unauthorized. The token might be expired. Re-authenticating...")
                    # Re-authenticate and update the token
                    main.auth_token = self.jit_authentication()
                    kwargs['headers']['authorization'] = f"Bearer {main.auth_token}"
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * backoff_factor
                    self.logger.warn(
                        f"Rate limit hit. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                elif response.status_code == 403:
                    self.logger.error("Access is forbidden.")
                    if "rate limit" in response.text.lower():
                        wait_time = (attempt + 1) * backoff_factor
                        self.logger.warn(
                            f"Rate limit possibly hit. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(
                            "Access is permanently forbidden. Exiting.")
                        exit(1)
                else:
                    self.logger.warn(
                        f"Request failed with status code {response.status_code}. Retrying...")
                    wait_time = (attempt + 1) * backoff_factor
                    time.sleep(wait_time)

            self.logger.error(
                f"Max retries reached. Request failed for URL: {args[0]}")
            return response
        return wrapper

    @ retry_request
    def send_request(url, method="GET", headers=None, json=None, params=None):
        session = requests.Session()
        retry = Retry(total=5, backoff_factor=1,
                      status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        session.mount('http://', adapter)

        if method == "GET":
            return session.get(url, headers=headers, params=params)
        elif method == "PATCH":
            return session.patch(url, headers=headers, json=json)
        elif method == "POST":
            return session.post(url, headers=headers, json=json)


if __name__ == "__main__":
    main()
