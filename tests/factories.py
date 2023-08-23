from collections import OrderedDict

from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory
from src.shared.consts import MANUAL_TEAM_SOURCE
from src.shared.models import TeamAttributes, TeamStructure, Asset, Organization, Resource, ResourceType

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


class ResourceFactory(ModelFactory):
    __model__ = Resource
    type = ResourceType.GithubRepo
    name = fake.word


class TeamStructureFactory(ModelFactory):
    __model__ = TeamStructure

    name = fake.word
    members = []
    resources = lambda: ResourceFactory.batch(3)


class OrganizationFactory(ModelFactory):
    __model__ = Organization

    teams = lambda: TeamStructureFactory.batch(3)


class AssetFactory(ModelFactory):
    __model__ = Asset

    asset_id = fake.uuid4
    tenant_id = fake.uuid4
    asset_type = "repo"
    vendor = "github"
    owner = "owner"
    asset_name = fake.word
    is_active = True
    is_covered = True
    is_archived = False
    created_at = fake.iso8601
    modified_at = fake.iso8601
