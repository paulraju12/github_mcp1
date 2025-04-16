from typing import Optional
from pydantic import BaseModel
from .utils import github_request, build_url

class SearchOptions(BaseModel):
    q: str
    order: Optional[str] = None
    page: Optional[int] = None
    per_page: Optional[int] = None

class SearchUsersOptions(SearchOptions):
    sort: Optional[str] = None

class SearchIssuesOptions(SearchOptions):
    sort: Optional[str] = None

async def search_code(params: SearchOptions) -> dict:
    url = build_url("https://api.github.com/search/code", params.dict(exclude_unset=True))
    return await github_request(url)

async def search_issues(params: SearchIssuesOptions) -> dict:
    url = build_url("https://api.github.com/search/issues", params.dict(exclude_unset=True))
    return await github_request(url)

async def search_users(params: SearchUsersOptions) -> dict:
    url = build_url("https://api.github.com/search/users", params.dict(exclude_unset=True))
    return await github_request(url)