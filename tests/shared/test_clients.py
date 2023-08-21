import pytest

from src.shared.clients.frontegg import get_jwt_token, FRONTEGG_AUTH_URL
from src.shared.clients.github import get_teams_from_github_topics
from src.shared.clients.jit import list_assets, get_existing_teams, create_teams, add_teams_to_asset, delete_teams
from src.shared.models import BaseTeam, Asset, Organization, TeamTemplate, Resource


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
             TeamTemplate(name="topic1", members=[], resources=[Resource(type="github_repo", name="repo1")]),
             TeamTemplate(name="topic2", members=[], resources=[Resource(type="github_repo", name="repo2")])
         ])),
        ([MockRepo("repo1", ["topic1"]), MockRepo("repo2", ["topic2"]), MockRepo("repo3", ["topic2"]),
          MockRepo("repo4", ["topic1", "topic2"])],
         Organization(teams=[
             TeamTemplate(name="topic1", members=[], resources=[
                 Resource(type="github_repo", name="repo1"),
                 Resource(type="github_repo", name="repo4")
             ]),
             TeamTemplate(name="topic2", members=[], resources=[
                 Resource(type="github_repo", name="repo2"),
                 Resource(type="github_repo", name="repo3"),
                 Resource(type="github_repo", name="repo4")
             ])
         ])),
    ]
)
def test_get_teams_from_github_topics(mock_repos, expected_result, mocker):
    # Mocking Github instance methods
    github_mock = mocker.Mock()
    organization_mock = mocker.Mock()

    # Mock the get_repos method to return the list of repositories
    organization_mock.get_repos.return_value = mock_repos

    github_mock.get_organization.return_value = organization_mock
    mocker.patch("src.shared.clients.github.Github", return_value=github_mock)  # Adjust the import path.

    # Run the function
    repositories = get_teams_from_github_topics()

    assert repositories == expected_result


def test_get_teams_from_github_topics_exception(mocker):
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

    requests_post_mock = mocker.patch("requests.post", return_value=response_mock)

    token = get_jwt_token()

    requests_post_mock.assert_called_once_with(
        FRONTEGG_AUTH_URL,
        json={"clientId": None, "secret": None},
        headers={"accept": "application/json", "content-type": "application/json"}
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
         [BaseTeam(tenant_id="tenant1", id="1", created_at="date1", modified_at="date2", name="name1"),
          BaseTeam(tenant_id="tenant2", id="2", created_at="date3", modified_at="date4", name="name2")]),
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
        (["team1", "team2"], [201, 201], ["Team 'team1' created successfully.", "Team 'team2' created successfully."]),
        (["team1", "team2"], [400, 201], ["Failed to create team 'team1'", "Team 'team2' created successfully."]),
    ]
)
def test_create_teams(mocker, teams_to_create, response_status_codes, log_messages):
    mock_responses = [mocker.MagicMock(status_code=code) for code in response_status_codes]
    mocker.patch("requests.post", side_effect=mock_responses)
    mock_logger_info = mocker.patch("loguru.logger.info")
    mock_logger_error = mocker.patch("loguru.logger.error")

    create_teams("test_token", teams_to_create)

    for message in log_messages:
        if "successfully" in message:
            mock_logger_info.assert_any_call(message)
        else:
            # check that the error message partially contains the expected message
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
        mock_logger_info.assert_called_once_with("Teams added to asset 'asset_id' successfully.")
    else:
        mock_logger_error.assert_called_once_with(expected_result.format(mock_response.text))


@pytest.mark.parametrize(
    "status_code, expected_result",
    [
        (204, "Team 'team1' deleted successfully."),
        (404, "Failed to delete team 'team2'. Status code: 404, {}"),
    ]
)
def test_delete_teams(mocker, status_code, expected_result):
    mock_existing_teams = [
        BaseTeam(tenant_id="tenant1", id="1", created_at="date1", modified_at="date2", name="team1"),
        BaseTeam(tenant_id="tenant2", id="2", created_at="date3", modified_at="date4", name="team2")
    ]
    mocker.patch("src.shared.clients.jit.get_existing_teams", return_value=mock_existing_teams)
    mock_responses = [mocker.MagicMock(status_code=status_code) for _ in range(2)]
    mocker.patch("requests.delete", side_effect=mock_responses)
    mock_logger_info = mocker.patch("loguru.logger.info")
    mock_logger_error = mocker.patch("loguru.logger.error")
    mock_logger_warning = mocker.patch("loguru.logger.warning")

    token = "test_token"
    team_names = ["team1", "team2"]

    delete_teams(token, team_names)

    mock_logger_info.assert_called_once_with(expected_result.format(""))
    if status_code == 404:
        mock_logger_error.assert_called_once_with(expected_result.format(""))
    else:
        mock_logger_error.assert_not_called()
    if status_code == 404:
        mock_logger_warning.assert_called_once_with("Team 'team2' not found.")
    else:
        mock_logger_warning.assert_not_called()
