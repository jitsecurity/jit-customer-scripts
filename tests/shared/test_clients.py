import json
import pytest
from src.shared.clients.github import get_teams_from_github_topics
from src.shared.clients.jit import list_assets, get_existing_teams, create_teams, add_teams_to_asset, delete_teams, \
    get_jit_jwt_token
from src.shared.env_tools import get_jit_endpoint_base_url
from src.shared.models import TeamAttributes, Asset, Organization, TeamStructure, Resource, ResourceType
from tests.factories import TeamAttributesFactory


class MockRepo:
    def __init__(self, name, topics):
        self.name = name
        self._topics = topics

    def get_topics(self):
        return self._topics


@pytest.mark.parametrize(
    "mock_repos, expected_result",
    [
        ([], Organization(teams=[])),
        ([MockRepo("repo1", [])], Organization(teams=[])),
        ([MockRepo("repo1", ["topic1"]), MockRepo("repo2", ["topic2"])],
         Organization(teams=[
             TeamStructure(name="topic1", members=[],
                           resources=[Resource(type=ResourceType.GithubRepo, name="repo1")]),
             TeamStructure(name="topic2", members=[],
                           resources=[Resource(type=ResourceType.GithubRepo, name="repo2")])
         ])),
        ([MockRepo("repo1", ["topic1"]), MockRepo("repo2", ["topic2"]), MockRepo("repo3", ["topic2"]),
          MockRepo("repo4", ["topic1", "topic2"])],
         Organization(teams=[
             TeamStructure(name="topic1", members=[], resources=[
                 Resource(type=ResourceType.GithubRepo, name="repo1"),
                 Resource(type=ResourceType.GithubRepo, name="repo4")
             ]),
             TeamStructure(name="topic2", members=[], resources=[
                 Resource(type=ResourceType.GithubRepo, name="repo2"),
                 Resource(type=ResourceType.GithubRepo, name="repo3"),
                 Resource(type=ResourceType.GithubRepo, name="repo4")
             ])
         ])),
    ]
)
def test_get_teams_from_github_topics__happy_flow(mock_repos, expected_result, mocker):
    # Mocking Github instance methods
    github_mock = mocker.Mock()
    organization_mock = mocker.Mock()

    # Mock the get_repos method to return the list of repositories
    organization_mock.get_repos.return_value = mock_repos

    github_mock.get_organization.return_value = organization_mock
    # Adjust the import path.
    mocker.patch("src.shared.clients.github.Github", return_value=github_mock)

    # Run the function
    repositories = get_teams_from_github_topics()

    assert repositories == expected_result


def test_get_teams_from_github_topics__exception_from_github(mocker):
    # Mocking Github to raise an exception
    mocker.patch("src.shared.clients.github.Github",
                 side_effect=Exception("Sample exception"))  # Adjust the import path.

    # Test that the function logs an error and returns None
    result = get_teams_from_github_topics()
    assert result == Organization(teams=[])


@pytest.mark.parametrize(
    "status_code, expected_result",
    [
        (200, "access_token"),
        (401, None),
        (500, None),
    ]
)
def test_get_jwt_token(status_code, expected_result, mocker):
    # Mocking the response
    response_mock = mocker.Mock()
    response_mock.status_code = status_code

    if status_code == 200:
        response_mock.json.return_value = {"accessToken": "access_token"}
    else:
        response_mock.json.return_value = {}

    requests_post_mock = mocker.patch(
        "requests.post", return_value=response_mock)

    token = get_jit_jwt_token()

    requests_post_mock.assert_called_once_with(
        f"{get_jit_endpoint_base_url()}/authentication/login",
        json={"clientId": None, "secret": None}
    )
    assert token == expected_result


@pytest.mark.parametrize(
    "status_code, response_data, expected_assets",
    [
        (200, [{"asset_id": "1", "tenant_id": "tenant1", "asset_type": "type1", "vendor": "vendor1", "owner": "owner1",
                "asset_name": "name1", "is_active": True, "created_at": "date1", "modified_at": "date2"}], [
            Asset(asset_id="1", tenant_id="tenant1", asset_type="type1", vendor="vendor1", owner="owner1",
                  asset_name="name1", is_active=True, created_at="date1", modified_at="date2")]),
        (400, {}, []),
    ]
)
def test_list_assets(mocker, status_code, response_data, expected_assets):
    mock_response = mocker.MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = response_data
    mocker.patch("requests.get", return_value=mock_response)

    result = list_assets("test_token")
    assert result == expected_assets


@pytest.mark.parametrize(
    "status_codes, response_data_list, expected_teams",
    [
        ([200, 200], [{"data": [
            {"tenant_id": "tenant1", "id": "1", "created_at": "date1", "modified_at": "date2", "name": "name1"}],
            "metadata": {"after": "some_value"}}, {"data": [
                {"tenant_id": "tenant2", "id": "2", "created_at": "date3", "modified_at": "date4", "name": "name2"}],
            "metadata": {"after": None}}],
         [TeamAttributes(tenant_id="tenant1", id="1", created_at="date1", modified_at="date2", name="name1"),
          TeamAttributes(tenant_id="tenant2", id="2", created_at="date3", modified_at="date4", name="name2")]),
        ([400], [{}], []),
    ]
)
def test_get_existing_teams(mocker, status_codes, response_data_list, expected_teams):
    mock_responses = [mocker.MagicMock(status_code=code, json=mocker.MagicMock(return_value=data)) for code, data in
                      zip(status_codes, response_data_list)]
    mocker.patch("requests.get", side_effect=mock_responses)

    result = get_existing_teams("test_token")
    assert result == expected_teams


@pytest.mark.parametrize(
    "teams_to_create, response_status_codes, log_messages",
    [
        (["team1", "team2"], [201, 201], [
            "Team 'team1' created successfully.", "Team 'team2' created successfully."]),
        (["team1", "team2"], [400, 201], [
            "Failed to create team 'team1'", "Team 'team2' created successfully."]),
    ]
)
def test_create_teams(mocker, teams_to_create, response_status_codes, log_messages):
    mock_responses = []
    for code in response_status_codes:
        if code == 201:
            mock_response = mocker.MagicMock(
                status_code=code,
                json=mocker.MagicMock(
                    return_value=TeamAttributesFactory().build().dict())
            )
        else:
            mock_response = mocker.MagicMock(
                status_code=code, json=mocker.MagicMock(return_value={}))
        mock_responses.append(mock_response)

    mocker.patch("requests.post", side_effect=mock_responses)
    mock_logger_info = mocker.patch("loguru.logger.info")
    mock_logger_error = mocker.patch("loguru.logger.error")

    create_teams("test_token", teams_to_create)

    for message in log_messages:
        if "successfully" in message:
            mock_logger_info.assert_any_call(message)
        else:
            assert [message in m for m in mock_logger_error.call_args.args][0]


@pytest.mark.parametrize(
    "status_code, expected_result",
    [
        (200, None),
        (400, "Failed to add teams to asset 'asset_id'. Status code: 400, {}"),
    ]
)
def test_add_teams_to_asset(mocker, status_code, expected_result):
    mock_response = mocker.MagicMock()
    mock_response.status_code = status_code
    mocker.patch("requests.patch", return_value=mock_response)
    mock_logger_info = mocker.patch("loguru.logger.info")
    mock_logger_error = mocker.patch("loguru.logger.error")

    asset = Asset(asset_id="asset_id", tenant_id="tenant_id", asset_type="asset_type", vendor="vendor",
                  owner="owner", asset_name="asset_name", is_active=True, created_at="created_at",
                  modified_at="modified_at")
    teams = ["team1", "team2"]

    add_teams_to_asset("test_token", asset, teams)

    if status_code == 200:
        mock_logger_info.assert_called_once_with(
            "Team(s) synced to asset 'asset_name' successfully.")
    else:
        mock_logger_error.assert_called_once_with(
            expected_result.format(mock_response.text))


@pytest.mark.parametrize(
    "status_code, existing_team_names, input_team_names, expected_info, expected_error, expected_warning",
    [
        (204, ["team1", "team2"], ["team1", "team2"],
         ["Team 'team1' deleted successfully.", "Team 'team2' deleted successfully."], [], []),
        (404, ["team1", "team2"], ["team1", "team2"], [],
         ["Failed to delete team 'team2'. Status code: 404, Error details."], []),
        (204, ["team1"], ["team1", "team2"], [
         "Team 'team1' deleted successfully."], [], ["Team 'team2' not found."])
    ]
)
def test_delete_teams(mocker, status_code, existing_team_names, input_team_names, expected_info, expected_error,
                      expected_warning):
    mock_existing_teams = [
        TeamAttributes(tenant_id=f"tenant{i + 1}", id=str(i + 1), created_at=f"date{i + 1}", modified_at=f"date{i + 2}",
                       name=team_name)
        for i, team_name in enumerate(existing_team_names)
    ]

    mocker.patch("src.shared.clients.jit.get_existing_teams",
                 return_value=mock_existing_teams)

    mock_responses = [mocker.MagicMock(
        status_code=status_code, text="Error details.") for _ in existing_team_names]
    mocker.patch("requests.delete", side_effect=mock_responses)

    mock_logger_info = mocker.patch("loguru.logger.info")
    mock_logger_error = mocker.patch("loguru.logger.error")
    mock_logger_warning = mocker.patch("loguru.logger.warning")

    token = "test_token"

    delete_teams(token, input_team_names)

    for msg in expected_info:
        mock_logger_info.assert_any_call(msg)
    for msg in expected_error:
        mock_logger_error.assert_any_call(msg)
    for msg in expected_warning:
        mock_logger_warning.assert_any_call(msg)
