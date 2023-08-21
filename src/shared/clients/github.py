import os
from typing import List, Optional

from dotenv import load_dotenv
from github import Github
from loguru import logger

from src.shared.models import RepositoryDetails

# Load environment variables from .env file. make sure it's before you import modules.
load_dotenv(".env")

ORGANIZATION_NAME = os.getenv("ORGANIZATION_NAME")
GITHUB_TOKEN = os.getenv("GITHUB_API_TOKEN")


def get_repos_from_github() -> Optional[List[RepositoryDetails]]:
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
        logger.error(f"Failed to retrieve teams: {str(e)}")
        return None
