import pytest

from src.scripts.sync_teams.sync_teams import get_teams_to_delete, get_teams_to_create


@pytest.mark.parametrize(
    "topic_names, existing_team_names, expected_result",
    [
        (["team1", "team2", "team3"], ["team1", "team2"], ["team3"]),
        (["team1", "team2"], ["team1", "team2", "team3"], []),
        (["team1", "team2", "team3"], [], ["team1", "team2", "team3"]),
        ([], ["team1", "team2", "team3"], []),
        ([], [], []),
    ]
)
def test_get_teams_to_create(topic_names, existing_team_names, expected_result):
    assert set(get_teams_to_create(topic_names, existing_team_names)) == set(expected_result)


@pytest.mark.parametrize(
    "topic_names, existing_team_names, expected_result",
    [
        (["team1", "team2", "team3"], ["team1", "team2"], []),
        (["team1", "team2"], ["team1", "team2", "team3"], ["team3"]),
        ([], ["team1", "team2", "team3"], ["team1", "team2", "team3"]),
        ([], [], []),
    ]
)
def test_get_teams_to_delete(topic_names, existing_team_names, expected_result):
    assert set(get_teams_to_delete(topic_names, existing_team_names)) == set(expected_result)
