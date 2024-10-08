from collections import OrderedDict
from json.decoder import JSONDecodeError
from unittest.mock import mock_open, patch

import pytest
from faker import Faker
from src.scripts.sync_teams.sync_teams import parse_input_file, update_assets
from src.scripts.sync_teams.sync_teams import process_teams
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
    "json_data, expected_teams, expected_skip_no_resources, expected_verify_github_membership",
    [
        ('{"teams": [{"name": "team1", "members": [], "resources": []}]}', 1, True, True),
        (
            '{"teams": [{"name": "team1", "members": [], "resources": []}, '
            '{"name": "team2", "members": [], "resources": []}]}',
            2, True, True
        ),
    ],
)
def test_parse_input_file(json_data, expected_teams, expected_skip_no_resources, expected_verify_github_membership):
    with patch("builtins.open", mock_open(read_data=json_data)):
        with patch("src.scripts.sync_teams.sync_teams.argparse.ArgumentParser.parse_args") as mock_parse_args:
            mock_parse_args.return_value.file = "tests/test_input.json"
            mock_parse_args.return_value.skip_no_resources = expected_skip_no_resources
            mock_parse_args.return_value.verify_github_membership = expected_verify_github_membership

            result, skip_no_resources, verify_github_membership = parse_input_file()

            assert isinstance(result, Organization)
            assert len(result.teams) == expected_teams
            assert skip_no_resources == expected_skip_no_resources
            assert verify_github_membership == expected_verify_github_membership


@pytest.mark.parametrize(
    "json_data, expected_teams, expected_skip_no_resources, expected_verify_github_membership",
    [
        ('{"teams": [{"name": "team1", "members": [], "resources": []}]}', 1, True, True),
        (
            '{"teams": [{"name": "team1", "members": [], "resources": []}, '
            '{"name": "team2", "members": [], "resources": []}]}',
            2, True, True
        ),
    ],
)
def test_parse_input_file(json_data, expected_teams, expected_skip_no_resources, expected_verify_github_membership):
    with patch("builtins.open", mock_open(read_data=json_data)):
        with patch("src.scripts.sync_teams.sync_teams.argparse.ArgumentParser.parse_args") as mock_parse_args:
            mock_parse_args.return_value.file = "tests/test_input.json"
            mock_parse_args.return_value.skip_no_resources = expected_skip_no_resources
            mock_parse_args.return_value.verify_github_membership = expected_verify_github_membership

            result, skip_no_resources, verify_github_membership = parse_input_file()

            assert isinstance(result, Organization)
            assert len(result.teams) == expected_teams
            assert skip_no_resources == expected_skip_no_resources
            assert verify_github_membership == expected_verify_github_membership


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
    "label, existing_teams_indexes, asset_indexes, len_expected_teams_to_delete, skip_no_resources",
    [
        ("No teams no assets", [], [], 0, True),
        ("No teams to create and no teams to delete", "all", "all", 0, True),
        ("No teams to create and teams to delete", "all", [0, 5], 8, True),
        ("Teams to create and no teams to delete", [0, 5], "all", 0, False),
    ]
)
def test_process_teams(label, existing_teams_indexes, asset_indexes, len_expected_teams_to_delete,
                       skip_no_resources, data):
    organization, assets, existing_teams = data
    existing_teams = [existing_teams[i]
                      for i in existing_teams_indexes] if existing_teams_indexes != "all" else existing_teams
    assets = [assets[i]
              for i in asset_indexes] if asset_indexes != "all" else assets

    with patch("src.scripts.sync_teams.sync_teams.get_existing_teams") as mock_get_existing_teams:
        with patch("src.scripts.sync_teams.sync_teams.create_teams") as mock_create_teams:
            mock_get_existing_teams.return_value = existing_teams
            teams_to_delete, created_teams = process_teams(
                "token", organization, assets, existing_teams, skip_no_resources)
            assert len(teams_to_delete) == len_expected_teams_to_delete


def test_update_assets(data):
    # Test with no assets
    organization, assets, teams = data
    # with patch("src.scripts.sync_teams.sync_teams.list_assets") as mock_list_assets:
    # mock_list_assets.return_value = []
    with patch("src.scripts.sync_teams.sync_teams.add_teams_to_asset") as mock_add_teams_to_asset:
        update_assets("token", assets, organization, teams)
        assert mock_add_teams_to_asset.call_count == 10
