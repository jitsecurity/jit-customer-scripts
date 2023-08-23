import os

from github import Github
from loguru import logger

from src.shared.models import TeamStructure, Resource, Organization, ResourceType


def get_teams_from_github_topics() -> Organization:
    try:
        logger.info(f"Trying to communicate with Github to get information from Org: {os.getenv('ORGANIZATION_NAME')}")
        # Create a GitHub instance using the token
        github = Github(os.getenv("GITHUB_API_TOKEN"))

        # Get the organization
        organization = github.get_organization(os.getenv('ORGANIZATION_NAME'))

        # Dictionary to store team templates
        teams = {}

        # Iterate over repositories in the organization
        for repo in organization.get_repos():
            # Get the repository name
            repo_name = repo.name

            # Get the repository topics
            topics = repo.get_topics()
            if not topics:
                continue

            # Iterate over each topic
            for topic in topics:
                # Check if the topic already exists in the teams dictionary
                if topic in teams:
                    # Add the repository to the existing team
                    teams[topic].resources.append(Resource(type=ResourceType.GithubRepo, name=repo_name))
                else:
                    # Create a new team template for the topic
                    team_template = TeamStructure(name=topic, members=[],
                                                  resources=[Resource(type=ResourceType.GithubRepo, name=repo_name)])

                    # Add the team template to the teams dictionary
                    teams[topic] = team_template

        logger.info(f"Retrieved ({len(teams.keys())}) team(s) {list(teams.keys())} from GitHub successfully.")
        return Organization(teams=list(teams.values()))
    except Exception as e:
        logger.error(f"Failed to retrieve teams from GitHub: {str(e)}")
        return Organization(teams=[])
