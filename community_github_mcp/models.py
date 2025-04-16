from typing import List, Optional
from pydantic import BaseModel

class GitHubAuthor(BaseModel):
    name: str
    email: str
    date: str

class GitHubOwner(BaseModel):
    login: str
    id: int
    node_id: str
    avatar_url: str
    url: str
    html_url: str
    type: str

class GitHubRepository(BaseModel):
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: GitHubOwner
    html_url: str
    description: Optional[str] = None
    fork: bool
    url: str
    created_at: str
    updated_at: str
    pushed_at: str
    git_url: str
    ssh_url: str
    clone_url: str
    default_branch: str
    parent: Optional[dict] = None
    source: Optional[dict] = None

class GitHubFileContentLinks(BaseModel):
    self: str
    git: Optional[str] = None
    html: Optional[str] = None

class GitHubFileContent(BaseModel):
    name: str
    path: str
    sha: str
    size: int
    url: str
    html_url: str
    git_url: str
    download_url: str
    type: str
    content: Optional[str] = None
    encoding: Optional[str] = None
    _links: GitHubFileContentLinks

class GitHubDirectoryContent(BaseModel):
    type: str
    size: int
    name: str
    path: str
    sha: str
    url: str
    git_url: str
    html_url: str
    download_url: Optional[str] = None

class GitHubContent(BaseModel):
    items: Optional[List[GitHubDirectoryContent]] = None
    name: Optional[str] = None
    path: Optional[str] = None
    sha: Optional[str] = None
    size: Optional[int] = None
    url: Optional[str] = None
    html_url: Optional[str] = None
    git_url: Optional[str] = None
    download_url: Optional[str] = None
    type: Optional[str] = None
    content: Optional[str] = None
    encoding: Optional[str] = None
    _links: Optional[GitHubFileContentLinks] = None

class GitHubTreeEntry(BaseModel):
    path: str
    mode: str
    type: str
    size: Optional[int] = None
    sha: str
    url: str

class GitHubTree(BaseModel):
    sha: str
    url: str
    tree: List[GitHubTreeEntry]
    truncated: bool

class GitHubCommit(BaseModel):
    sha: str
    node_id: str
    url: str
    author: GitHubAuthor
    committer: GitHubAuthor
    message: str
    tree: dict
    parents: List[dict]

class GitHubReference(BaseModel):
    ref: str
    node_id: str
    url: str
    object: dict

class GitHubIssueAssignee(BaseModel):
    login: str
    id: int
    avatar_url: str
    url: str
    html_url: str

class GitHubLabel(BaseModel):
    id: int
    node_id: str
    url: str
    name: str
    color: str
    default: bool
    description: Optional[str] = None

class GitHubMilestone(BaseModel):
    url: str
    html_url: str
    labels_url: str
    id: int
    node_id: str
    number: int
    title: str
    description: str
    state: str

class GitHubIssue(BaseModel):
    url: str
    repository_url: str
    labels_url: str
    comments_url: str
    events_url: str
    html_url: str
    id: int
    node_id: str
    number: int
    title: str
    user: GitHubIssueAssignee
    labels: List[GitHubLabel]
    state: str
    locked: bool
    assignee: Optional[GitHubIssueAssignee] = None
    assignees: List[GitHubIssueAssignee]
    milestone: Optional[GitHubMilestone] = None
    comments: int
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    body: Optional[str] = None

class GitHubSearchResponse(BaseModel):
    total_count: int
    incomplete_results: bool
    items: List[GitHubRepository]

class GitHubPullRequestRef(BaseModel):
    label: str
    ref: str
    sha: str
    user: GitHubIssueAssignee
    repo: GitHubRepository

class GitHubPullRequest(BaseModel):
    url: str
    id: int
    node_id: str
    html_url: str
    diff_url: str
    patch_url: str
    issue_url: str
    number: int
    state: str
    locked: bool
    title: str
    user: GitHubIssueAssignee
    body: Optional[str] = None
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    merged_at: Optional[str] = None
    merge_commit_sha: Optional[str] = None
    assignee: Optional[GitHubIssueAssignee] = None
    assignees: List[GitHubIssueAssignee]
    requested_reviewers: List[GitHubIssueAssignee]
    labels: List[GitHubLabel]
    head: GitHubPullRequestRef
    base: GitHubPullRequestRef