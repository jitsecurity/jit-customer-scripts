"""
GitLab Team Resource Manager

This script manages team resources in GitLab by automatically updating asset
coverage in the JIT platform. It processes team metadata from multiple JSON
files to identify resources and updates their coverage status based on
matching criteria.

Flow:
1. Authenticates with JIT API
2. Reads team metadata from all JSON files in the specified directory
3. Fetches uncovered assets from JIT API
4. Matches assets with team resources
5. Updates coverage status for matching assets (up to 100 assets total)

The script uses pagination to handle large numbers of assets and includes
retry logic for API requests to handle temporary failures.
"""

import os
import json
import requests
import logging
import sys
import glob
from typing import List, Dict
from dataclasses import dataclass
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Disable logging from the requests library
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Constants
MAX_RETRIES = 5
RETRY_BACKOFF_FACTOR = 2
ASSETS_PER_PAGE = 100
JIT_API_ENDPOINT = "https://api.jit.io"
MAX_ASSETS_TO_UPDATE = 100  # Limit to 100 assets total


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
    Manages JIT assets including authentication, fetching, and updating
    coverage.

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
        
        # Remove any existing handlers to avoid duplicate logs
        if logger.handlers:
            for handler in logger.handlers:
                logger.removeHandler(handler)
                
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
        
        # Prevent propagation to the root logger to avoid duplicate logs
        logger.propagate = False
        
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


def load_team_metadata_files(directory_path: str, logger=None) -> List[Team]:
    """
    Loads all team metadata JSON files from the specified directory.

    Args:
        directory_path: Path to directory containing team metadata JSON files
        logger: Logger instance to use for logging (optional)

    Returns:
        List[Team]: Combined list of all teams from all JSON files
    """
    all_teams = []
    
    # Use provided logger or fall back to root logger
    log = logger or logging.getLogger()

    # Get all JSON files in the directory
    json_files = sorted(glob.glob(os.path.join(directory_path, "*.json")))

    if not json_files:
        return all_teams

    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                team_data = json.load(f)
                team_metadata = TeamMetadata.from_dict(team_data)
                all_teams.extend(team_metadata.teams)
                file_name = os.path.basename(json_file)
                log.info(
                    f"Loaded {len(team_metadata.teams)} teams from {file_name}"
                )
        except Exception as e:
            log.error(
                f"Failed to read team metadata file {json_file}: {str(e)}"
            )

    return all_teams


def main():
    """
    Main execution function for the GitLab Team Resource Manager.

    Process:
    1. Validates environment variables and configuration
    2. Initializes JIT Asset Manager
    3. Authenticates with JIT API
    4. Reads and parses team metadata from all JSON files in the directory
    5. Fetches uncovered assets
    6. Processes teams in order, updating up to 100 assets total
    7. Excludes archived assets

    Exit codes:
        0: Success or no action needed
        1: Error occurred (missing config, authentication failure, etc.)
    """
    # Get credentials from environment variables
    client_id = os.getenv("JIT_CLIENT_ID")
    client_secret = os.getenv("JIT_CLIENT_SECRET")
    metadata_path = "src/scripts/gitlab_team_resource_manager"

    if not all([client_id, client_secret]):
        print("Error: Missing required environment variables")
        print("Required: JIT_CLIENT_ID, JIT_CLIENT_SECRET")
        sys.exit(1)

    # Initialize the asset manager
    manager = JitAssetManager(client_id, client_secret)

    # Configure root logger to use the same format
    root_logger = logging.getLogger()
    # Remove any existing handlers
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Authenticate
    if not manager.authenticate():
        sys.exit(1)

    # Load all team metadata files
    teams = load_team_metadata_files(metadata_path, manager.logger)

    if not teams:
        manager.logger.info("No teams found in metadata files")
        sys.exit(0)

    manager.logger.info(f"Loaded {len(teams)} teams from all metadata files")

    # Get all assets first
    assets = manager.get_all_assets()
    if not assets:
        manager.logger.error("No assets found")
        sys.exit(1)

    # Filter out archived assets
    active_assets = [
        asset for asset in assets
        if not asset.get("is_archived", False)
    ]
    manager.logger.info(
        "Filtered %d assets, removed %d archived assets",
        len(active_assets),
        len(assets) - len(active_assets)
    )

    # Use only active assets from now on
    assets = active_assets

    # Extract all asset names from the assets
    asset_names = [asset.get("asset_name", "") for asset in assets]
    manager.logger.info("Found %d active assets", len(asset_names))

    # Process teams until we reach MAX_ASSETS_TO_UPDATE assets or run out of
    # teams
    assets_to_update = []
    processed_teams = []
    # Track processed asset IDs to avoid duplicates
    processed_asset_ids = set()
    # Track total assets per team for reporting
    team_asset_counts = {}

    for team in teams:
        if not team.resources:
            continue

        # Check if any resource name is in the assets
        resource_names = [r.name for r in team.resources]
        matching_resources = [
            name for name in resource_names if name in asset_names
        ]

        if not matching_resources:
            continue

        # Found a team with matching resources
        manager.logger.info(
            "Found team with matching resources: %s", team.name
        )
        manager.logger.info(
            "Matching resources: %d/%d",
            len(matching_resources),
            len(resource_names)
        )

        # Get all assets for this team that haven't been processed yet
        team_assets = []
        # Count total assets related to this team
        total_team_assets = 0

        for asset in assets:
            asset_name = asset.get("asset_name", "")
            if asset_name in resource_names:
                total_team_assets += 1

                asset_id = asset.get("asset_id")
                if asset_id not in processed_asset_ids:
                    team_assets.append({
                        "asset_id": asset_id,
                        "is_covered": True,
                        "tags": []
                    })
                    processed_asset_ids.add(asset_id)

                    # Break if we've reached our limit
                    if (len(assets_to_update) + len(team_assets) >=
                            MAX_ASSETS_TO_UPDATE):
                        manager.logger.info(
                            f"Reached limit of {MAX_ASSETS_TO_UPDATE} "
                            f"assets to update"
                        )
                        break

        # Store the total assets count for this team
        team_asset_counts[team.name] = total_team_assets

        # If we found assets to update for this team
        if team_assets:
            # Check if adding all team assets would exceed our limit
            assets_to_add = team_assets
            if len(assets_to_update) + len(team_assets) > MAX_ASSETS_TO_UPDATE:
                # Only add up to the limit
                remaining_slots = MAX_ASSETS_TO_UPDATE - len(assets_to_update)
                assets_to_add = team_assets[:remaining_slots]
                manager.logger.info(
                    f"Partially processing team '{team.name}' - "
                    f"adding {len(assets_to_add)} of {len(team_assets)} assets"
                )
            else:
                manager.logger.info(
                    f"Processing all {len(team_assets)} assets for team "
                    f"'{team.name}'"
                )

            # Add this team's assets to our update list
            assets_to_update.extend(assets_to_add)
            processed_teams.append({
                "team": team,
                "count": len(assets_to_add),
                "total": total_team_assets
            })

            manager.logger.info(
                "Added %d assets from team '%s', total: %d",
                len(assets_to_add),
                team.name,
                len(assets_to_update)
            )

            # If we've reached our limit, stop processing teams
            if len(assets_to_update) >= MAX_ASSETS_TO_UPDATE:
                manager.logger.info(
                    f"Reached limit of {MAX_ASSETS_TO_UPDATE} assets to update"
                )
                break

    # Update the assets if we have any
    if assets_to_update:
        total_count = len(assets_to_update)

        # Log summary for each team
        manager.logger.info(
            "======================================== TEAM UPDATE SUMMARY ========================================"
        )
        for team_info in processed_teams:
            team_name = team_info["team"].name
            updated_count = team_info["count"]
            total_count_team = team_info["total"]
            percentage = 0
            if total_count_team > 0:
                percentage = updated_count / total_count_team * 100
            manager.logger.info(
                "Team '%s': %d/%d assets (%.1f%%)",
                team_name,
                updated_count,
                total_count_team,
                percentage
            )
        manager.logger.info(
            "Total assets to update: %d",
            total_count
        )

        # Perform the update
        success = manager.update_asset_coverage(assets_to_update)

        if success:
            manager.logger.info(
                "UPDATE COMPLETE: Successfully updated %d assets",
                total_count
            )
            for team_info in processed_teams:
                team_name = team_info["team"].name
                updated_count = team_info["count"]
                total_count_team = team_info["total"]
                percentage = 0
                if total_count_team > 0:
                    percentage = updated_count / total_count_team * 100
                manager.logger.info(
                    "- Team '%s': %d/%d assets (%.1f%%)",
                    team_name,
                    updated_count,
                    total_count_team,
                    percentage
                )
        else:
            manager.logger.error(
                "UPDATE FAILED: Failed to update %d assets",
                total_count
            )
    else:
        manager.logger.info("NO UPDATES NEEDED: No assets to update")


if __name__ == "__main__":
    main()
