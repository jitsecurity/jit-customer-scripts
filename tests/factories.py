from collections import OrderedDict

from faker import Faker
from src.shared.consts import MANUAL_TEAM_SOURCE
from polyfactory.factories.pydantic_factory import ModelFactory
from src.shared.models import TeamAttributes, TeamStructure, Asset, Organization

locales = OrderedDict([
    ('en-US', 1),
])
Faker.seed(10)
fake = Faker(locales)


class TeamAttributesFactory(ModelFactory):
    __model__ = TeamAttributes

    tenant_id = fake.uuid4
    id = fake.uuid4
    created_at = fake.iso8601
    modified_at = fake.iso8601
    name = fake.word
    description = fake.sentence
    parent_team_id = fake.uuid4
    children_team_ids = []
    score = lambda: fake.random_int(min=1, max=100)
    source = MANUAL_TEAM_SOURCE


class TeamStructureFactory(ModelFactory):
    __model__ = TeamStructure

    tenant_id = fake.uuid4
    team_id = fake.uuid4
    parent_team_id = fake.uuid4
    children_team_ids = []


class AssetFactory(ModelFactory):
    __model__ = Asset

    tenant_id = fake.uuid4
    id = fake.uuid4
    name = fake.word
    description = fake.sentence
    team_id = fake.uuid4


class OrganizationFactory(ModelFactory):
    __model__ = Organization

    tenant_id = fake.uuid4
    id = fake.uuid4
    name = fake.word
    description = fake.sentence
    assets = []
    teams = []
