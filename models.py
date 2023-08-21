from typing import Optional, List

from pydantic import BaseModel

from consts import MANUAL_TEAM_SOURCE


class RepositoryDetails(BaseModel):
    name: str
    topics: List[str]


class BaseTeam(BaseModel):
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
