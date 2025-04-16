import base64
from typing import List, Optional
from pydantic import BaseModel, Field
from .utils import github_request
from .models import GitHubContent, GitHubAuthor, GitHubTree, GitHubCommit, GitHubReference, GitHubFileContent
from .errors import GitHubResourceNotFoundError

# Schema definitions
class FileOperation(BaseModel):
    path: str
    content: str

class CreateOrUpdateFileInput(BaseModel):
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="Path where to create/update the file")
    content: str = Field(..., description="Content of the file")
    message: str = Field(..., description="Commit message")
    branch: str = Field(..., description="Branch to create/update the file in")
    sha: Optional[str] = Field(None, description="SHA of the file being replaced")

class GetFileContentsInput(BaseModel):
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="Path to the file or directory")
    branch: Optional[str] = Field(None, description="Branch to get contents from")

class PushFilesInput(BaseModel):
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(..., description="Branch to push to")
    files: List[FileOperation] = Field(..., description="Array of files to push")
    message: str = Field(..., description="Commit message")

class GitHubCreateUpdateFileResponse(BaseModel):
    content: Optional[GitHubFileContent]
    commit: dict

async def get_file_contents(owner: str, repo: str, path: str, branch: Optional[str] = None) -> GitHubContent:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    if branch:
        url += f"?ref={branch}"
    response = await github_request(url)
    if isinstance(response, dict) and "content" in response:
        response["content"] = base64.b64decode(response["content"]).decode("utf-8")
    return GitHubContent(**response) if isinstance(response, dict) else GitHubContent(items=response)

async def create_or_update_file(
    owner: str, repo: str, path: str, content: str, message: str, branch: str, sha: Optional[str] = None
) -> GitHubCreateUpdateFileResponse:
    encoded_content = base64.b64encode(content.encode()).decode()
    body = {"message": message, "content": encoded_content, "branch": branch}
    if not sha:
        try:
            existing_file = await get_file_contents(owner, repo, path, branch)
            if not isinstance(existing_file, list):
                body["sha"] = existing_file.sha
        except GitHubResourceNotFoundError:
            pass
    else:
        body["sha"] = sha

    response = await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
        method="PUT",
        json=body
    )
    return GitHubCreateUpdateFileResponse(**response)

async def create_tree(owner: str, repo: str, files: List[FileOperation], base_tree: Optional[str] = None) -> GitHubTree:
    tree = [{"path": f.path, "mode": "100644", "type": "blob", "content": f.content} for f in files]
    response = await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees",
        method="POST",
        json={"tree": tree, "base_tree": base_tree}
    )
    return GitHubTree(**response)

async def create_commit(owner: str, repo: str, message: str, tree: str, parents: List[str]) -> GitHubCommit:
    response = await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/git/commits",
        method="POST",
        json={"message": message, "tree": tree, "parents": parents}
    )
    return GitHubCommit(**response)

async def update_reference(owner: str, repo: str, ref: str, sha: str) -> GitHubReference:
    response = await github_request(
        f"https://api.github.com/repos/{owner}/{repo}/git/refs/{ref}",
        method="PATCH",
        json={"sha": sha, "force": True}
    )
    return GitHubReference(**response)

async def push_files(owner: str, repo: str, branch: str, files: List[FileOperation], message: str) -> GitHubReference:
    ref_response = await github_request(f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}")
    ref = GitHubReference(**ref_response)
    commit_sha = ref.object["sha"]
    tree = await create_tree(owner, repo, files, commit_sha)
    commit = await create_commit(owner, repo, message, tree.sha, [commit_sha])
    return await update_reference(owner, repo, f"heads/{branch}", commit.sha)