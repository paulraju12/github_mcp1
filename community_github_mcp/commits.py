from typing import Optional
from pydantic import BaseModel
from .utils import github_request, build_url

class ListCommitsInput(BaseModel):
    owner: str
    repo: str
    sha: Optional[str] = None
    page: Optional[int] = None
    per_page: Optional[int] = None

async def list_commits(
    owner: str, repo: str, page: Optional[int] = None, per_page: Optional[int] = None, sha: Optional[str] = None
) -> list:
    url = build_url(
        f"https://api.github.com/repos/{owner}/{repo}/commits",
        {"page": page, "per_page": per_page, "sha": sha}
    )
    return await github_request(url)