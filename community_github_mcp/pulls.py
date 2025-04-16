from typing import List, Optional
from pydantic import BaseModel, Field
from .utils import github_request, build_url
from .models import GitHubPullRequest, GitHubIssueAssignee, GitHubRepository

class PullRequestFile(BaseModel):
    sha: str
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    blob_url: str
    raw_url: str
    contents_url: str
    patch: Optional[str] = None

class StatusCheck(BaseModel):
    url: str
    state: str
    description: Optional[str] = None
    target_url: Optional[str] = None
    context: str
    created_at: str
    updated_at: str

class CombinedStatus(BaseModel):
    state: str
    statuses: List[StatusCheck]
    sha: str
    total_count: int

class PullRequestComment(BaseModel):
    url: str
    id: int
    node_id: str
    pull_request_review_id: Optional[int] = None
    diff_hunk: str
    path: Optional[str] = None
    position: Optional[int] = None
    original_position: Optional[int] = None
    commit_id: str
    original_commit_id: str
    user: GitHubIssueAssignee
    body: str
    created_at: str
    updated_at: str
    html_url: str
    pull_request_url: str
    author_association: str
    _links: dict

class PullRequestReview(BaseModel):
    id: int
    node_id: str
    user: GitHubIssueAssignee
    body: Optional[str] = None
    state: str
    html_url: str
    pull_request_url: str
    commit_id: str
    submitted_at: Optional[str] = None
    author_association: str

class CreatePullRequestInput(BaseModel):
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="Pull request title")
    body: Optional[str] = Field(None, description="Pull request body/description")
    head: str = Field(..., description="The name of the branch where your changes are implemented")
    base: str = Field(..., description="The name of the branch you want the changes pulled into")
    draft: Optional[bool] = Field(None, description="Whether to create the pull request as a draft")
    maintainer_can_modify: Optional[bool] = Field(None, description="Whether maintainers can modify the pull request")

class GetPullRequestInput(BaseModel):
    owner: str
    repo: str
    pull_number: int

class ListPullRequestsInput(BaseModel):
    owner: str
    repo: str
    state: Optional[str] = None
    head: Optional[str] = None
    base: Optional[str] = None
    sort: Optional[str] = None
    direction: Optional[str] = None
    per_page: Optional[int] = None
    page: Optional[int] = None

class CreatePullRequestReviewInput(BaseModel):
    owner: str
    repo: str
    pull_number: int
    commit_id: Optional[str] = None
    body: str
    event: str
    comments: Optional[List[dict]] = None

class MergePullRequestInput(BaseModel):
    owner: str
    repo: str
    pull_number: int
    commit_title: Optional[str] = None
    commit_message: Optional[str] = None
    merge_method: Optional[str] = None

class GetPullRequestFilesInput(BaseModel):
    owner: str
    repo: str
    pull_number: int

class GetPullRequestStatusInput(BaseModel):
    owner: str
    repo: str
    pull_number: int

class UpdatePullRequestBranchInput(BaseModel):
    owner: str
    repo: str
    pull_number: int
    expected_head_sha: Optional[str] = None

class GetPullRequestCommentsInput(BaseModel):
    owner: str
    repo: str
    pull_number: int

class GetPullRequestReviewsInput(BaseModel):
    owner: str
    repo: str
    pull_number: int

async def create_pull_request(params: CreatePullRequestInput) -> GitHubPullRequest:
    response = await github_request(
        f"https://api.github.com/repos/{params.owner}/{params.repo}/pulls",
        method="POST",
        json=params.dict(exclude_unset=True)
    )
    return GitHubPullRequest(**response)

async def get_pull_request(owner: str, repo: str, pull_number: int) -> GitHubPullRequest:
    response = await github_request(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}")
    return GitHubPullRequest(**response)

async def list_pull_requests(owner: str, repo: str, options: dict) -> List[GitHubPullRequest]:
    url = build_url(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        options
    )
    response = await github_request(url)
    return [GitHubPullRequest(**pr) for pr in response]

async def create_pull_request_review(owner: str, repo: str, pull_number: int, options: dict) -> PullRequestReview:
    response = await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
        method="POST",
        json=options
    )
    return PullRequestReview(**response)

async def merge_pull_request(owner: str, repo: str, pull_number: int, options: dict) -> dict:
    return await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/merge",
        method="PUT",
        json=options
    )

async def get_pull_request_files(owner: str, repo: str, pull_number: int) -> List[PullRequestFile]:
    response = await github_request(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files")
    return [PullRequestFile(**file) for file in response]

async def update_pull_request_branch(
    owner: str, repo: str, pull_number: int, expected_head_sha: Optional[str] = None
) -> None:
    body = {"expected_head_sha": expected_head_sha} if expected_head_sha else {}
    await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/update-branch",
        method="PUT",
        json=body
    )

async def get_pull_request_comments(owner: str, repo: str, pull_number: int) -> List[PullRequestComment]:
    response = await github_request(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/comments")
    return [PullRequestComment(**comment) for comment in response]

async def get_pull_request_reviews(owner: str, repo: str, pull_number: int) -> List[PullRequestReview]:
    response = await github_request(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews")
    return [PullRequestReview(**review) for review in response]

async def get_pull_request_status(owner: str, repo: str, pull_number: int) -> CombinedStatus:
    pr = await get_pull_request(owner, repo, pull_number)
    response = await github_request(f"https://api.github.com/repos/{owner}/{repo}/commits/{pr.head.sha}/status")
    return CombinedStatus(**response)