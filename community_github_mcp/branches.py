from typing import Optional
from pydantic import BaseModel, Field
from .utils import github_request
from .models import GitHubReference
from .errors import GitHubResourceNotFoundError

# Schema definitions
class CreateBranchOptions(BaseModel):
    ref: str
    sha: str

class CreateBranchInput(BaseModel):
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(..., description="Name for the new branch")
    from_branch: Optional[str] = Field(None, description="Source branch to create from")

async def get_default_branch_sha(owner: str, repo: str) -> str:
    try:
        response = await github_request(f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/main")
        return GitHubReference(**response).object["sha"]
    except GitHubResourceNotFoundError:
        response = await github_request(f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/master")
        return GitHubReference(**response).object["sha"]

async def create_branch(owner: str, repo: str, options: CreateBranchOptions) -> GitHubReference:
    full_ref = f"refs/heads/{options.ref}"
    response = await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/git/refs",
        method="POST",
        json={"ref": full_ref, "sha": options.sha}
    )
    return GitHubReference(**response)

async def get_branch_sha(owner: str, repo: str, branch: str) -> str:
    response = await github_request(f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}")
    return GitHubReference(**response).object["sha"]

async def create_branch_from_ref(
    owner: str, repo: str, new_branch: str, from_branch: Optional[str] = None
) -> GitHubReference:
    sha = await get_branch_sha(owner, repo, from_branch) if from_branch else await get_default_branch_sha(owner, repo)
    return await create_branch(owner, repo, CreateBranchOptions(ref=new_branch, sha=sha))

async def update_branch(owner: str, repo: str, branch: str, sha: str) -> GitHubReference:
    response = await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}",
        method="PATCH",
        json={"sha": sha, "force": True}
    )
    return GitHubReference(**response)