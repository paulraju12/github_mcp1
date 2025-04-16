import sys
import os
from contextlib import asynccontextmanager

import anyio
import uvicorn
# from sse_starlette import sse
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server.sse import SseServerTransport

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import asyncio
import logging
import httpx
from functools import wraps
from typing import Callable, Any
from mcp.server.fastmcp import FastMCP, Context
from community_github_mcp.utils import set_organization_id, get_organization_id, fetch_pat_token
from pydantic import ValidationError
from community_github_mcp import (
    repository,
    files,
    issues,
    pulls,
    branches,
    search,
    commits
)
from community_github_mcp.errors import (
    GitHubError,
    GitHubValidationError,
    GitHubResourceNotFoundError,
    GitHubAuthenticationError,
    GitHubPermissionError,
    GitHubRateLimitError,
    GitHubConflictError
)
from community_github_mcp.version import VERSION

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

mcp = FastMCP("github-mcp-server", dependencies=["httpx", "pydantic"])
sse = SseServerTransport("/messages")

# Custom errors
class MissingOrganizationIdError(Exception):
    def __init__(self):
        super().__init__("Missing X-Organization-Id header")
        self.status = 400

# Decorator to extract organization ID
def with_organization_id(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, ctx: Any = None, **kwargs) -> Any:
        organization_id = None
        if ctx and hasattr(ctx, "request") and hasattr(ctx.request, "headers"):
            organization_id = ctx.request.headers.get("X-Organization-Id")
            if organization_id:
                logger.debug(f"Using X-Organization-Id from headers: {organization_id}")
        # Fallback to hardcoded organizationId
        if not organization_id:
            organization_id = "a1fb0a19-a3dd-43f4-99b8-fa9108ab17f3"
            logger.debug("No header provided, using fallback organizationId")
        if not organization_id:
            logger.error("No organizationId available")
            raise ValueError("No organizationId available")
        logger.debug(f"Setting thread-local organization_id: {organization_id}")
        set_organization_id(organization_id)
        try:
            return await func(*args, **kwargs)
        finally:
            logger.debug("Clearing thread-local organization_id")
            set_organization_id(None)

    return wrapper

# Format GitHub errors
def format_github_error(error: GitHubError) -> str:
    message = f"GitHub API Error: {error.message}"
    if isinstance(error, GitHubValidationError):
        message = f"Validation Error: {error.message}"
        if error.response:
            message += f"\nDetails: {error.response}"
    elif isinstance(error, GitHubResourceNotFoundError):
        message = f"Not Found: {error.message}"
    elif isinstance(error, GitHubAuthenticationError):
        message = f"Authentication Failed: {error.message}"
    elif isinstance(error, GitHubPermissionError):
        message = f"Permission Denied: {error.message}"
    elif isinstance(error, GitHubRateLimitError):
        message = f"Rate Limit Exceeded: {error.message}\nResets at: {error.reset_at}"
    elif isinstance(error, GitHubConflictError):
        message = f"Conflict: {error.message}"
    return message

# FastMCP tools
@mcp.tool()
@with_organization_id
async def create_branch(params: branches.CreateBranchInput) -> str:
    """Create a new branch in a GitHub repository"""
    try:
        result = await branches.create_branch_from_ref(
            params.owner,
            params.repo,
            params.branch,
            params.from_branch
        )
        return str(result.dict())
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def list_commits(params: commits.ListCommitsInput) -> str:
    """Get list of commits of a branch in a GitHub repository"""
    try:
        result = await commits.list_commits(
            params.owner,
            params.repo,
            params.page,
            params.per_page,
            params.sha
        )
        return str(result)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def create_or_update_file(params: files.CreateOrUpdateFileInput) -> str:
    """Create or update a single file in a GitHub repository"""
    try:
        result = await files.create_or_update_file(
            params.owner,
            params.repo,
            params.path,
            params.content,
            params.message,
            params.branch,
            params.sha
        )
        return str(result.dict())
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def get_file_contents(params: files.GetFileContentsInput) -> str:
    """Get the contents of a file or directory from a GitHub repository"""
    try:
        result = await files.get_file_contents(
            params.owner,
            params.repo,
            params.path,
            params.branch
        )
        return str(result.dict() if hasattr(result, 'dict') else result)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def push_files(params: files.PushFilesInput) -> str:
    """Push multiple files to a GitHub repository in a single commit"""
    try:
        result = await files.push_files(
            params.owner,
            params.repo,
            params.branch,
            params.files,
            params.message
        )
        return str(result.dict())
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def create_issue(params: issues.CreateIssueInput) -> str:
    """Create a new issue in a GitHub repository"""
    try:
        options = issues.CreateIssueOptions(**params.dict(exclude={"owner", "repo"}))
        result = await issues.create_issue(params.owner, params.repo, options)
        return str(result)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def get_issue(params: issues.GetIssueInput) -> str:
    """Get details of a specific issue in a GitHub repository"""
    try:
        result = await issues.get_issue(params.owner, params.repo, params.issue_number)
        return str(result)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def list_issues(params: issues.ListIssuesOptions) -> str:
    """List issues in a GitHub repository with filtering options"""
    try:
        result = await issues.list_issues(params.owner, params.repo, params)
        return str(result)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def update_issue(params: issues.UpdateIssueInput) -> str:
    """Update an existing issue in a GitHub repository"""
    try:
        options = issues.UpdateIssueOptions(**params.dict(exclude={"owner", "repo", "issue_number"}))
        result = await issues.update_issue(params.owner, params.repo, params.issue_number, options)
        return str(result)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def add_issue_comment(params: issues.IssueCommentInput) -> str:
    """Add a comment to an existing issue"""
    try:
        result = await issues.add_issue_comment(params.owner, params.repo, params.issue_number, params.body)
        return str(result)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def create_pull_request(params: pulls.CreatePullRequestInput) -> str:
    """Create a new pull request in a GitHub repository"""
    try:
        result = await pulls.create_pull_request(params)
        return str(result.dict())
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def get_pull_request(params: pulls.GetPullRequestInput) -> str:
    """Get details of a specific pull request"""
    try:
        result = await pulls.get_pull_request(params.owner, params.repo, params.pull_number)
        return str(result.dict())
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def list_pull_requests(params: pulls.ListPullRequestsInput) -> str:
    """List and filter repository pull requests"""
    try:
        options = params.dict(exclude={"owner", "repo"}, exclude_unset=True)
        result = await pulls.list_pull_requests(params.owner, params.repo, options)
        return str([r.dict() for r in result])
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def create_pull_request_review(params: pulls.CreatePullRequestReviewInput) -> str:
    """Create a review on a pull request"""
    try:
        options = params.dict(exclude={"owner", "repo", "pull_number"}, exclude_unset=True)
        result = await pulls.create_pull_request_review(params.owner, params.repo, params.pull_number, options)
        return str(result.dict())
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def merge_pull_request(params: pulls.MergePullRequestInput) -> str:
    """Merge a pull request"""
    try:
        options = params.dict(exclude={"owner", "repo", "pull_number"}, exclude_unset=True)
        result = await pulls.merge_pull_request(params.owner, params.repo, params.pull_number, options)
        return str(result)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def get_pull_request_files(params: pulls.GetPullRequestFilesInput) -> str:
    """Get the list of files changed in a pull request"""
    try:
        result = await pulls.get_pull_request_files(params.owner, params.repo, params.pull_number)
        return str([r.dict() for r in result])
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def get_pull_request_status(params: pulls.GetPullRequestStatusInput) -> str:
    """Get the combined status of all status checks for a pull request"""
    try:
        result = await pulls.get_pull_request_status(params.owner, params.repo, params.pull_number)
        return str(result.dict())
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def update_pull_request_branch(params: pulls.UpdatePullRequestBranchInput) -> str:
    """Update a pull request branch with the latest changes from the base branch"""
    try:
        await pulls.update_pull_request_branch(params.owner, params.repo, params.pull_number, params.expected_head_sha)
        return str({"success": True})
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def get_pull_request_comments(params: pulls.GetPullRequestCommentsInput) -> str:
    """Get the review comments on a pull request"""
    try:
        result = await pulls.get_pull_request_comments(params.owner, params.repo, params.pull_number)
        return str([r.dict() for r in result])
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def get_pull_request_reviews(params: pulls.GetPullRequestReviewsInput) -> str:
    """Get the reviews on a pull request"""
    try:
        result = await pulls.get_pull_request_reviews(params.owner, params.repo, params.pull_number)
        return str([r.dict() for r in result])
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def create_repository(params: repository.CreateRepositoryOptions) -> str:
    """Create a new GitHub repository in your account"""
    try:
        result = await repository.create_repository(params)
        return str(result.dict())
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def search_repositories(params: repository.SearchRepositoriesInput) -> str:
    """Search for GitHub repositories"""
    try:
        result = await repository.search_repositories(params.query, params.page, params.per_page)
        return str(result.dict())
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def fork_repository(params: repository.ForkRepositoryInput) -> str:
    """Fork a GitHub repository to your account or specified organization"""
    try:
        result = await repository.fork_repository(params.owner, params.repo, params.organization)
        return str(result.dict())
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def search_code(params: search.SearchOptions) -> str:
    """Search for code across GitHub repositories"""
    try:
        result = await search.search_code(params)
        return str(result)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def search_issues(params: search.SearchIssuesOptions) -> str:
    """Search for issues and pull requests across GitHub repositories"""
    try:
        result = await search.search_issues(params)
        return str(result)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))

@mcp.tool()
@with_organization_id
async def search_users(params: search.SearchUsersOptions) -> str:
    """Search for users on GitHub"""
    try:
        result = await search.search_users(params)
        return str(result)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    except GitHubError as e:
        raise RuntimeError(format_github_error(e))


if __name__ =="__main__":
    mcp.settings.port=3005
    mcp.run(transport="sse")




# @asynccontextmanager
# async def mcp_lifecycle():
#     logger.info("Initializing MCP server")
#     try:
#         yield
#     finally:
#         logger.info("Cleaning up MCP server")
#
# async def main():
#     async with mcp_lifecycle():
#         async with anyio.create_task_group() as tg:
#             logger.debug("Starting MCP server task")
#             tg.start_soon(mcp.run_stdio_async)
#             try:
#                 # Keep task group alive
#                 await anyio.sleep_forever()
#             except anyio.get_cancelled_exc_class():
#                 logger.debug("Task group cancelled")
#                 raise
#
# if __name__ == "__main__":
#     logger.info("Starting GitHub MCP server")
#     try:
#         anyio.run(main)
#     except KeyboardInterrupt:
#         logger.info("Server stopped by user")
#     except Exception as e:
#         logger.error(f"Server failed to start: {e}")
#         raise

