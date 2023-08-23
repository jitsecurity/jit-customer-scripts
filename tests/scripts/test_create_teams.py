from collections import OrderedDict
from json.decoder import JSONDecodeError
from unittest.mock import patch

import pytest
from faker import Faker
from src.scripts.create_teams import parse_input_file, update_assets
from src.scripts.create_teams import process_teams
from src.shared.models import Organization
from tests.factories import AssetFactory, TeamAttributesFactory, TeamStructureFactory
from tests.factories import OrganizationFactory

locales = OrderedDict([
    ('en-US', 1),
])
Faker.seed(10)
fake = Faker(locales)


@pytest.fixture
def organization():
    return OrganizationFactory.batch(3)


@pytest.mark.parametrize(
    "json_data, expected_teams",
    [
        ('{"teams": [{"name": "team1", "members": [], "resources": []}]}', 1),
        (
                '{"teams": [{"name": "team1", "members": [], "resources": []}, '
                '{"name": "team2", "members": [], "resources": []}]}',
                2,
        ),
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
                False,
                "",
        ),  # not an organization data
    ],
)
def test_parse_input_file__with_invalid_json(invalid_file, json_data, should_raise, expected_exception):
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
                parse_input_file()
                assert exc_info.value.code == 1


@pytest.fixture
def data():
    Faker.seed(10)
    num_objects = 10
    organization = Organization(teams=TeamStructureFactory.batch(num_objects))
    assets = AssetFactory.batch(num_objects, asset_name=fake.word())
    teams = TeamAttributesFactory.batch(num_objects)

    for i in range(num_objects):
        assets[i].asset_name = organization.teams[i].resources[0].name
    for i in range(num_objects):
        teams[i].name = [t.name for t in organization.teams][i]
    return organization, assets, teams


@pytest.mark.parametrize(
    "label, existing_teams_indexes, asset_indexes, len_expected_teams_to_delete",
    [
        ("No teams no assets", [], [], 0),
        ("No teams to create and no teams to delete", "all", "all", 0),
        ("No teams to create and teams to delete", "all", [0, 5], 8),
        ("Teams to create and no teams to delete", [0, 5], "all", 0),
    ]
)
def test_process_teams(label, existing_teams_indexes, asset_indexes, data, len_expected_teams_to_delete):
    organization, assets, existing_teams = data
    existing_teams = [existing_teams[i] for i in
                      existing_teams_indexes] if existing_teams_indexes != "all" else existing_teams
    assets = [assets[i] for i in
              asset_indexes] if asset_indexes != "all" else assets

    with patch("src.scripts.create_teams.get_existing_teams") as mock_get_existing_teams:
        with patch("src.scripts.create_teams.create_teams") as mock_create_teams:
            mock_get_existing_teams.return_value = existing_teams
            teams_to_delete = process_teams("token", organization, assets)
            assert len(teams_to_delete) == len_expected_teams_to_delete


def test_update_assets(data):
    # Test with no assets
    organization, assets, teams = data
    # with patch("src.scripts.create_teams.list_assets") as mock_list_assets:
    # mock_list_assets.return_value = []
    with patch("src.scripts.create_teams.add_teams_to_asset") as mock_add_teams_to_asset:
        update_assets("token", assets, organization)
        assert mock_add_teams_to_asset.call_count == 10
