from typing import Optional
from pydantic import BaseModel, Field
from .utils import github_request
from .models import GitHubRepository, GitHubSearchResponse

class CreateRepositoryOptions(BaseModel):
    name: str = Field(..., description="Repository name")
    description: Optional[str] = Field(None, description="Repository description")
    private: Optional[bool] = Field(None, description="Whether the repository should be private")
    auto_init: Optional[bool] = Field(None, description="Initialize with README.md")

class SearchRepositoriesInput(BaseModel):
    query: str = Field(..., description="Search query")
    page: Optional[int] = Field(1, description="Page number for pagination")
    per_page: Optional[int] = Field(30, description="Number of results per page")

class ForkRepositoryInput(BaseModel):
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    organization: Optional[str] = Field(None, description="Optional organization to fork to")

async def create_repository(options: CreateRepositoryOptions) -> GitHubRepository:
    response = await github_request(
        "https://api.github.com/user/repos",
        method="POST",
        json=options.dict(exclude_unset=True)
    )
    return GitHubRepository(**response)

async def search_repositories(query: str, page: int = 1, per_page: int = 30) -> GitHubSearchResponse:
    url = f"https://api.github.com/search/repositories?q={query}&page={page}&per_page={per_page}"
    response = await github_request(url)
    return GitHubSearchResponse(**response)

async def fork_repository(owner: str, repo: str, organization: Optional[str] = None) -> GitHubRepository:
    url = f"https://api.github.com/repos/{owner}/{repo}/forks"
    if organization:
        url += f"?organization={organization}"
    response = await github_request(url, method="POST")
    return GitHubRepository(**response, parent=response.get("parent"), source=response.get("source"))