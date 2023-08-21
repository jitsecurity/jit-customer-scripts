import pytest

from clients.frontegg import get_jwt_token, FRONTEGG_AUTH_URL
from clients.github import get_repos_from_github
from models import RepositoryDetails


# Sample data
class MockRepo:
    def __init__(self, name, topics):
        self.name = name
        self._topics = topics

    def get_topics(self):
        return self._topics


@pytest.mark.parametrize(
    "mock_repos, expected_result",
    [
        ([], []),
        ([MockRepo("repo1", [])], []),
        ([MockRepo("repo1", ["topic1"]), MockRepo("repo2", ["topic2"])],
         [RepositoryDetails(name="repo1", topics=["topic1"]), RepositoryDetails(name="repo2", topics=["topic2"])]),
    ]
)
def test_get_repos_from_github(mock_repos, expected_result, mocker):
    # Mocking Github instance methods
    github_mock = mocker.Mock()
    organization_mock = mocker.Mock()

    organization_mock.get_repos.return_value = mock_repos
    github_mock.get_organization.return_value = organization_mock
    mocker.patch("clients.github.Github", return_value=github_mock)  # Adjust the import path.

    # Run the function
    repositories = get_repos_from_github()

    assert repositories == expected_result


def test_get_repos_from_github_exception(mocker):
    # Mocking Github to raise an exception
    mocker.patch("clients.github.Github", side_effect=Exception("Sample exception"))  # Adjust the import path.

    # Test that the function logs an error and returns None
    result = get_repos_from_github()
    assert result is None


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
