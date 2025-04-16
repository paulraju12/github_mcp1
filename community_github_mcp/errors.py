from typing import Any, Optional

class GitHubError(Exception):
    def __init__(self, message: str, status: int, response: Any = None):
        super().__init__(message)
        self.status = status
        self.response = response
        self.name = "GitHubError"

class GitHubValidationError(GitHubError):
    def __init__(self, message: str, status: int, response: Any = None):
        super().__init__(message, status, response)
        self.name = "GitHubValidationError"

class GitHubResourceNotFoundError(GitHubError):
    def __init__(self, resource: str):
        super().__init__(f"Resource not found: {resource}", 404, {"message": f"{resource} not found"})
        self.name = "GitHubResourceNotFoundError"

class GitHubAuthenticationError(GitHubError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401, {"message": message})
        self.name = "GitHubAuthenticationError"

class GitHubPermissionError(GitHubError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, 403, {"message": message})
        self.name = "GitHubPermissionError"

class GitHubRateLimitError(GitHubError):
    def __init__(self, message: str = "Rate limit exceeded", reset_at: str = ""):
        super().__init__(message, 429, {"message": message, "reset_at": reset_at})
        self.name = "GitHubRateLimitError"
        self.reset_at = reset_at

class GitHubConflictError(GitHubError):
    def __init__(self, message: str):
        super().__init__(message, 409, {"message": message})
        self.name = "GitHubConflictError"

def create_github_error(status: int, response: Any) -> GitHubError:
    message = response.get("message", "GitHub API error") if isinstance(response, dict) else "GitHub API error"
    if status == 401:
        return GitHubAuthenticationError(message)
    elif status == 403:
        return GitHubPermissionError(message)
    elif status == 404:
        return GitHubResourceNotFoundError(message)
    elif status == 409:
        return GitHubConflictError(message)
    elif status == 422:
        return GitHubValidationError(message, status, response)
    elif status == 429:
        reset_at = response.get("reset_at", "") if isinstance(response, dict) else ""
        return GitHubRateLimitError(message, reset_at)
    return GitHubError(message, status, response)