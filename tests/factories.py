from collections import OrderedDict

from faker import Faker
from src.shared.consts import MANUAL_TEAM_SOURCE

locales = OrderedDict([
    ('en-US', 1),
])
Faker.seed(10)
fake = Faker(locales)

from polyfactory.factories.pydantic_factory import ModelFactory
from src.shared.models import TeamAttributes


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


if __name__ == '__main__':
    print(TeamAttributesFactory.batch(size=3))