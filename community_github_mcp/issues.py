from typing import List, Optional
from pydantic import BaseModel
from .utils import github_request, build_url

class GetIssueInput(BaseModel):
    owner: str
    repo: str
    issue_number: int

class IssueCommentInput(BaseModel):
    owner: str
    repo: str
    issue_number: int
    body: str

class CreateIssueOptions(BaseModel):
    title: str
    body: Optional[str] = None
    assignees: Optional[List[str]] = None
    milestone: Optional[int] = None
    labels: Optional[List[str]] = None

class CreateIssueInput(CreateIssueOptions):
    owner: str
    repo: str

class ListIssuesOptions(BaseModel):
    direction: Optional[str] = None
    labels: Optional[List[str]] = None
    page: Optional[int] = None
    per_page: Optional[int] = None
    since: Optional[str] = None
    sort: Optional[str] = None
    state: Optional[str] = None

class UpdateIssueOptions(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    assignees: Optional[List[str]] = None
    milestone: Optional[int] = None
    labels: Optional[List[str]] = None
    state: Optional[str] = None

class UpdateIssueInput(UpdateIssueOptions):
    owner: str
    repo: str
    issue_number: int

async def get_issue(owner: str, repo: str, issue_number: int) -> dict:
    return await github_request(f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}")

async def add_issue_comment(owner: str, repo: str, issue_number: int, body: str) -> dict:
    return await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
        method="POST",
        json={"body": body}
    )

async def create_issue(owner: str, repo: str, options: CreateIssueOptions) -> dict:
    return await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/issues",
        method="POST",
        json=options.dict(exclude_unset=True)
    )

async def list_issues(owner: str, repo: str, options: ListIssuesOptions) -> list:
    url = build_url(
        f"https://api.github.com/repos/{owner}/{repo}/issues",
        {
            "direction": options.direction,
            "labels": ",".join(options.labels) if options.labels else None,
            "page": options.page,
            "per_page": options.per_page,
            "since": options.since,
            "sort": options.sort,
            "state": options.state
        }
    )
    return await github_request(url)

async def update_issue(owner: str, repo: str, issue_number: int, options: UpdateIssueOptions) -> dict:
    return await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}",
        method="PATCH",
        json=options.dict(exclude_unset=True)
    )