from enum import Enum
from typing import Optional, List

from pydantic import BaseModel
from src.shared.consts import MANUAL_TEAM_SOURCE


class ResourceType(str, Enum):
    GithubRepo = 'github_repo'


class TeamAttributes(BaseModel):
    tenant_id: str
    id: str
    created_at: str
    modified_at: str
    name: str
    description: Optional[str] = None
    parent_team_id: Optional[str] = None
    children_team_ids: List[str] = []
    score: int = 0
    source: str = MANUAL_TEAM_SOURCE


class Resource(BaseModel):
    type: str
    name: str


class TeamStructure(BaseModel):
    name: str
    members: List[str] = []
    resources: List[Resource] = []


class Tag(BaseModel):
    name: str
    value: str


class Asset(BaseModel):
    asset_id: str
    tenant_id: str
    asset_type: str
    vendor: str
    owner: str
    asset_name: str
    is_active: bool
    is_covered: bool = True
    is_archived: Optional[bool] = False
    created_at: str
    modified_at: str
    tags: Optional[List[Tag]] = []


class Organization(BaseModel):
    teams: List[TeamStructure]


class MemberMapping(BaseModel):
    team_name: str
    members: List[str]
