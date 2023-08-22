from json.decoder import JSONDecodeError
from unittest.mock import patch

import pytest

from src.scripts.create_teams import parse_input_file, process_teams, update_assets
from src.shared.models import Organization, TeamStructure


@pytest.fixture
def organization():
    return Organization(
        teams=[
            TeamStructure(name="team1", members=[], resources=[]),
            TeamStructure(name="team2", members=[], resources=[]),
        ]
    )


@pytest.mark.parametrize(
    "json_data, expected_teams",
    [
        ('{"teams": [{"name": "team1", "members": [], "resources": []}]}', 1),
        (
                '{"teams": [{"name": "team1", "members": [], "resources": []}, '
                '{"name": "team2", "members": [], "resources": []}]}',
                2),
    ],
)
def test_parse_input_file(json_data, expected_teams):
    with open("test_input.json", "w") as file:
        file.write(json_data)
    with patch("src.scripts.create_teams.argparse.ArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value.file = "test_input.json"
        result = parse_input_file()
        assert len(result.teams) == expected_teams


@pytest.mark.parametrize(
    "invalid_file, json_data, should_raise, expected_exception",
    [
        ("", "", False, ""),  # No file provided
        ("test_input.txt", "some text", False, ""),  # Wrong file type provided
        (
            "test_input.json",
            '{"teams": [{"name": "team1", "members": [], "resources": []}',
            True,
            JSONDecodeError,
        ),  # Malformed JSON data
        (
            "test_input.json",
            '{"name": "team1", "members": [], "resources": []}',
            True,
            KeyError,
        ),  # not an organization data
    ],
)
def test_parse_input_file_with_invalid_json(invalid_file, json_data, should_raise, expected_exception):
    if invalid_file:
        with open(invalid_file, "w") as file:
            file.write(json_data)
    with patch("src.scripts.create_teams.argparse.ArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value.file = invalid_file
        if should_raise:
            with pytest.raises(expected_exception) as exc_info:
                parse_input_file()
            assert isinstance(exc_info.value, expected_exception)
        else:
            with pytest.raises(SystemExit) as exc_info:
                result = parse_input_file()
                assert exc_info.value.code == 1


def test_process_teams(organization):
    # Test with no existing teams
    with patch("src.scripts.create_teams.get_existing_teams") as mock_get_existing_teams:
        mock_get_existing_teams.return_value = []
        result = process_teams("token", organization)
        assert len(result) == 0

    # Test with some existing teams
    with patch("src.scripts.create_teams.get_existing_teams") as mock_get_existing_teams:
        mock_get_existing_teams.return_value = [
            TeamStructure(name="team1", members=[], resources=[]),
            TeamStructure(name="team3", members=[], resources=[]),
        ]
        result = process_teams("token", organization)
        assert len(result) == 1
        assert result[0] == "team3"


def test_update_assets(organization):
    # Test with no assets
    with patch("src.scripts.create_teams.list_assets") as mock_list_assets:
        mock_list_assets.return_value = []
        update_assets("token", organization)

    # Test with some assets
    with patch("src.scripts.create_teams.list_assets") as mock_list_assets:
        mock_list_assets.return_value = [
            TeamStructure(name="team1", members=[], resources=[]),
            TeamStructure(name="team2", members=[], resources=[]),
        ]
        with patch("src.scripts.create_teams.get_teams_for_assets") as mock_get_teams_for_assets:
            mock_get_teams_for_assets.return_value = {
                "asset1": ["team1"],
                "asset2": ["team1", "team2"],
            }
            with patch("src.scripts.create_teams.add_teams_to_asset") as mock_add_teams_to_asset:
                update_assets("token", organization)
                assert mock_add_teams_to_asset.call_count == 2
