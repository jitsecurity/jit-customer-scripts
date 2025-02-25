"""
GitLab Team Resource Manager

This script manages team resources in GitLab by automatically updating asset
coverage in the JIT platform. It processes team metadata to identify resources
and updates their coverage status based on matching criteria.

Flow:
1. Authenticates with JIT API
2. Reads team metadata from JSON file
3. Fetches uncovered assets from JIT API
4. Matches assets with team resources
5. Updates coverage status for matching assets

The script uses pagination to handle large numbers of assets and includes
retry logic for API requests to handle temporary failures.
"""

import os
import json
import requests
import logging
import sys
from typing import List, Dict
from dataclasses import dataclass
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants
MAX_RETRIES = 5
RETRY_BACKOFF_FACTOR = 2
ASSETS_PER_PAGE = 100
JIT_API_ENDPOINT = "https://api.jit.io"


@dataclass
class Resource:
    """
    Represents a team resource with its type, name, and vendor.
    
    Attributes:
        type: The type of resource (e.g., 'repository')
        name: The name of the resource
        vendor: The vendor of the resource (e.g., 'gitlab')
    """
    type: str
    name: str
    vendor: str


@dataclass
class Team:
    """
    Represents a team with its name, members, and resources.
    
    Attributes:
        name: The name of the team
        members: List of team member identifiers
        resources: List of Resource objects associated with the team
    """
    name: str
    members: List[str]
    resources: List[Resource]


@dataclass
class TeamMetadata:
    """
    Contains metadata for all teams.
    
    Attributes:
        teams: List of Team objects
    """
    teams: List[Team]

    @classmethod
    def from_dict(cls, data: Dict) -> "TeamMetadata":
        """
        Creates a TeamMetadata instance from a dictionary.
        
        Args:
            data: Dict containing team data with structure:
                 {
                     "teams": [
                         {
                             "name": str,
                             "members": List[str],
                             "resources": List[Dict]
                         }
                     ]
                 }
        
        Returns:
            TeamMetadata instance populated with the provided data
        """
        teams = []
        for team_data in data.get("teams", []):
            resources = [
                Resource(type=r["type"], name=r["name"], vendor=r["vendor"])
                for r in team_data.get("resources", [])
            ]
            team = Team(
                name=team_data["name"],
                members=team_data.get("members", []),
                resources=resources,
            )
            teams.append(team)
        return cls(teams=teams)


class JitAssetManager:
    """
    Manages JIT assets including authentication, fetching, and updating coverage.
    
    This class handles all interactions with the JIT API, including:
    - Authentication using client credentials
    - Fetching assets with pagination
    - Updating asset coverage status
    - Retry logic for API requests
    
    Attributes:
        client_id: JIT API client ID
        client_secret: JIT API client secret
        token: Authentication token (set after successful auth)
        logger: Configured logger instance
    """

    def __init__(self, client_id: str, client_secret: str):
        """
        Initializes the JIT Asset Manager.
        
        Args:
            client_id: JIT API client ID
            client_secret: JIT API client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        Configures and returns a logger instance.
        
        Returns:
            Configured logging.Logger instance
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
        return logger

    def authenticate(self) -> bool:
        """
        Authenticates with JIT API using client credentials.
        
        Performs authentication using the provided client ID and secret.
        Sets the token attribute upon successful authentication.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        auth_url = f"{JIT_API_ENDPOINT}/authentication/login"
        auth_payload = {
            "clientId": self.client_id,
            "secret": self.client_secret
        }
        auth_headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }

        try:
            response = self._send_request(
                url=auth_url,
                method="POST",
                headers=auth_headers,
                json=auth_payload
            )
            if response.status_code == 200:
                self.token = response.json().get("accessToken")
                self.logger.info("Authentication successful")
                return True
            else:
                self.logger.error(
                    "Authentication failed with status code: %d",
                    response.status_code
                )
                return False
        except Exception as e:
            self.logger.error("Authentication failed: %s", str(e))
            return False

    def get_all_assets(self) -> List[Dict]:
        """
        Fetches all uncovered assets using pagination.
        
        Makes paginated requests to the JIT API to fetch all uncovered assets.
        Handles pagination using the 'after' parameter from response metadata.
        
        Returns:
            List[Dict]: List of asset dictionaries containing asset details
        """
        if not self.token:
            self.logger.error("No authentication token available")
            return []

        assets = []
        after = None  # Start with no after parameter for the first page

        while True:
            url = f"{JIT_API_ENDPOINT}/asset"
            headers = {
                "accept": "application/json, text/plain, */*",
                "authorization": f"Bearer {self.token}",
                "api_version": "v2",
            }

            # Only include after parameter if we have one
            params = {"limit": ASSETS_PER_PAGE, "is_covered": False}
            if after:
                params["after"] = after

            try:
                self.logger.info("Fetching assets page")
                response = self._send_request(
                    url=url,
                    headers=headers,
                    params=params
                )
                if response.status_code != 200:
                    self.logger.error(
                        "Failed to fetch assets: %d",
                        response.status_code
                    )
                    break
                data = response.json()

                assets.extend(data["data"])
                total_assets = len(assets)
                self.logger.info(
                    "Fetched %d assets, total: %d",
                    len(data),
                    total_assets
                )

                after = data["metadata"]["after"]
                if not after:
                    break
                self.logger.info(f"After: {after}")

                # Check if we've fetched all available assets
                if len(data["data"]) < ASSETS_PER_PAGE:
                    self.logger.info("Received fewer assets than limit")
                    break

            except Exception as e:
                self.logger.error("Error fetching assets: %s", str(e))
                break

        self.logger.info(f"Completed fetching assets, total: {len(assets)}")
        return assets

    def update_asset_coverage(self, asset_updates: List[Dict]) -> bool:
        """
        Updates coverage status for multiple assets.
        
        Args:
            asset_updates: List of dictionaries with structure:
                         [
                             {
                                 "asset_id": str,
                                 "is_covered": bool,
                                 "tags": List[str]
                             }
                         ]
        
        Returns:
            bool: True if update successful, False otherwise
        """
        if not self.token:
            self.logger.error("No authentication token available")
            return False

        url = f"{JIT_API_ENDPOINT}/asset/assets"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        }

        try:
            response = self._send_request(
                url=url,
                method="POST",
                headers=headers,
                json=asset_updates
            )
            if response.status_code == 200:
                self.logger.info(
                    "Successfully updated %d assets",
                    len(asset_updates)
                )
                return True
            else:
                self.logger.error(
                    "Failed to update assets: %d",
                    response.status_code
                )
                return False
        except Exception as e:
            self.logger.error("Error updating assets: %s", str(e))
            return False

    def _send_request(
        self, url: str, method: str = "GET", **kwargs
    ) -> requests.Response:
        """
        Sends HTTP request with retry logic.
        
        Configures and sends HTTP requests with automatic retries for failed
        requests. Uses exponential backoff for retries.
        
        Args:
            url: Target URL for the request
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments passed to requests.request()
        
        Returns:
            requests.Response: Response from the API
        """
        session = requests.Session()
        retry = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session.request(method, url, **kwargs)


def main():
    """
    Main execution function for the GitLab Team Resource Manager.
    
    Process:
    1. Validates environment variables and configuration
    2. Initializes JIT Asset Manager
    3. Authenticates with JIT API
    4. Reads and parses team metadata
    5. Fetches uncovered assets
    6. Finds first team with matching resources
    7. Updates coverage for matching assets
    
    Exit codes:
        0: Success or no action needed
        1: Error occurred (missing config, authentication failure, etc.)
    """
    # Get credentials from environment variables
    client_id = os.getenv("JIT_CLIENT_ID")
    client_secret = os.getenv("JIT_CLIENT_SECRET")
    metadata_path = "src/scripts/gitlab_team_resource_manager"
    team_metadata_file = f"{metadata_path}/team_metadata.json"

    if not all([client_id, client_secret, team_metadata_file]):
        print("Error: Missing required environment variables")
        print("Required: JIT_CLIENT_ID, JIT_CLIENT_SECRET, TEAM_METADATA_FILE")
        sys.exit(1)

    # Initialize the asset manager
    manager = JitAssetManager(client_id, client_secret)

    # Authenticate
    if not manager.authenticate():
        sys.exit(1)

    # Read team metadata
    try:
        with open(team_metadata_file, "r") as f:
            team_data = json.load(f)
            team_metadata = TeamMetadata.from_dict(team_data)
    except Exception as e:
        manager.logger.error("Failed to read team metadata file: %s", str(e))
        sys.exit(1)

    if not team_metadata.teams:
        manager.logger.info("No teams found in metadata")
        sys.exit(0)

    # Get all assets first
    assets = manager.get_all_assets()
    if not assets:
        manager.logger.error("No assets found")
        sys.exit(1)

    # Extract all asset names from the assets
    asset_names = [asset.get("asset_name", "") for asset in assets]
    manager.logger.info("Found %d assets", len(asset_names))

    # Find the first team with resources that match assets
    target_team = None
    for team in team_metadata.teams:
        if not team.resources:
            continue
        # Check if any resource name is in the assets
        resource_names = [r.name for r in team.resources]
        matching_resources = [
            name for name in resource_names if name in asset_names
        ]
        if matching_resources:
            target_team = team
            manager.logger.info(
                "Found team with matching resources: %s", team.name
            )
            manager.logger.info(
                "Matching resources: %s", matching_resources
            )
            break

    if not target_team:
        manager.logger.info("No team with matching resources found")
        sys.exit(0)

    manager.logger.info("Processing team: %s", target_team.name)

    # Get resource names for the target team
    resource_names = [r.name for r in target_team.resources]
    manager.logger.info("Team members: %s", target_team.members)
    manager.logger.info("Team resources: %s", resource_names)

    # Update coverage for matching assets
    assets_to_update = []
    for asset in assets:
        if asset.get("asset_name") in resource_names:
            manager.logger.info("Updating asset: %s", asset["asset_id"])
            assets_to_update.append(
                {"asset_id": asset["asset_id"], "is_covered": True, "tags": []}
            )

    if assets_to_update:
        count = len(assets_to_update)
        manager.logger.info("Updating coverage for %d assets", count)
        manager.update_asset_coverage(assets_to_update)
    else:
        manager.logger.info("No assets need coverage update")


if __name__ == "__main__":
    main()
