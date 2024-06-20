import os

from google.cloud import bigquery
from google.oauth2 import service_account
from loguru import logger

from src.shared.models import TeamStructure, Resource, Organization, ResourceType

bigquery_view_name = os.getenv('BIGQUERY_VIEW_NAME')
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')


def get_teams_from_bigquery_view() -> Organization:
    try:
        num_repos = 0
        logger.info(
            f"Retrieving teams from BigQuery View: {os.getenv('BIGQUERY_VIEW_NAME')}")

        # Explicitly use service account credentials by specifying the private key file.
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path)
        client = bigquery.Client(credentials=credentials)

        teams = {}
        fields = [
            "ownership_team_name",
            "repos",
            "managers",
            "manager_usernames",
            "members",
            "member_usernames",
            "slack_alerting_channel"
        ]

        # Perform a query
        query = "SELECT {fields} FROM `{view}` WHERE ARRAY_LENGTH(repos)>0 AND NOT CONTAINS_SUBSTR(ownership_team_name, 'Kaluza')".format(
            fields=", ".join(fields), view=bigquery_view_name)
        query_job = client.query(query)  # API request
        rows = query_job.result()  # Waits for query to finish

        for row in rows:
            resources = [Resource(type=ResourceType.GithubRepo, name=repo)
                         for repo in row.repos]
            num_repos += len(resources)
            members = row.manager_usernames + row.member_usernames
            teams[row.ownership_team_name] = TeamStructure(
                name=row.ownership_team_name, members=members, resources=resources, slack_channel=row.slack_alerting_channel)
        logger.info(
            f"Retrieved ({len(teams.keys())}) teams {list(teams.keys())} with {num_repos} repos from Google BigQuery successfully.")
        return Organization(teams=list(teams.values()))
    except Exception as e:
        logger.error(f"Failed to retrieve teams from GitHub: {str(e)}")
        return Organization(teams=[])
