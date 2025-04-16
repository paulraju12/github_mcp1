import httpx
import threading
from typing import Any, Dict, Optional
from .errors import create_github_error
from .version import VERSION

_thread_local = threading.local()
_organization_lock = threading.Lock()

hardcoded_token = "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"  # Redacted in response

def set_organization_id(organization_id: Optional[str]) -> None:
    """Set the organization ID for the current thread."""
    with _organization_lock:
        setattr(_thread_local, 'organization_id', organization_id)

def get_organization_id() -> Optional[str]:
    """Get the organization ID for the current thread."""
    return getattr(_thread_local, 'organization_id', None)

async def fetch_pat_token(organization_id: str) -> str:
    """Fetch PAT token using organization ID."""
    if not organization_id:
        raise ValueError("No organization ID provided")
    payload = {
        "organizationId": organization_id,
        "serviceId": "github-mcp-service",
        "type": "MCP"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://auth-service.example.com/token",
                json=payload,
                timeout=5.0
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("token")
            if not token:
                raise ValueError("No token in response")
            return token
    except httpx.HTTPStatusError as e:
        raise ValueError(f"HTTP {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        raise ValueError(f"Network error: {str(e)}")

async def github_request(
        url: str,
        method: str = "GET",
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        token: Optional[str] = None
) -> Any:
    default_headers = {
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": f"modelcontextprotocol/servers/github/v{VERSION}",
    }
    effective_token = token
    if not effective_token:
        org_id = get_organization_id()
        if org_id:
            try:
                effective_token = await fetch_pat_token(org_id)
            except Exception as e:
                print(f"Failed to fetch PAT: {e}")
                effective_token = None
        if not effective_token:
            effective_token = hardcoded_token
            print("Using fallback hardcoded PAT")
    if not effective_token:
        raise ValueError("No authentication token provided")
    default_headers["Authorization"] = f"Bearer {effective_token}"
    headers = {**default_headers, **(headers or {})}
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, json=json, headers=headers)
        if not response.is_success:
            try:
                error_data = response.json()
                raise create_github_error(response.status_code, error_data)
            except ValueError:
                raise create_github_error(response.status_code, {"message": "Failed to parse error response"})
        return response.json()

def build_url(base_url: str, params: Dict[str, Any]) -> str:
    import urllib.parse
    filtered_params = {k: v for k, v in params.items() if v is not None}
    query = urllib.parse.urlencode(filtered_params)
    return f"{base_url}?{query}" if query else base_url

def validate_branch_name(branch: str) -> str:
    sanitized = branch.strip()
    if not sanitized:
        raise ValueError("Branch name cannot be empty")
    if ".." in sanitized:
        raise ValueError("Branch name cannot contain '..'")
    if any(c in sanitized for c in " ~^:?*[\\]"):
        raise ValueError("Branch name contains invalid characters")
    if sanitized.startswith("/") or sanitized.endswith("/"):
        raise ValueError("Branch name cannot start or end with '/'")
    if sanitized.endswith(".lock"):
        raise ValueError("Branch name cannot end with '.lock'")
    return sanitized

def validate_repository_name(name: str) -> str:
    sanitized = name.strip().lower()
    if not sanitized:
        raise ValueError("Repository name cannot be empty")
    if not all(c.isalnum() or c in "_-." for c in sanitized):
        raise ValueError("Repository name can only contain lowercase letters, numbers, hyphens, periods, and underscores")
    if sanitized.startswith(".") or sanitized.endswith("."):
        raise ValueError("Repository name cannot start or end with a period")
    return sanitized

def validate_owner_name(owner: str) -> str:
    sanitized = owner.strip().lower()
    if not sanitized:
        raise ValueError("Owner name cannot be empty")
    if not (sanitized[0].isalnum() and len(sanitized) <= 39):
        raise ValueError("Owner name must start with a letter or number and can contain up to 39 characters")
    return sanitized

async def check_branch_exists(owner: str, repo: str, branch: str) -> bool:
    try:
        await github_request(f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}")
        return True
    except Exception as e:
        if hasattr(e, "status") and e.status == 404:
            return False
        raise

async def check_user_exists(username: str) -> bool:
    try:
        await github_request(f"https://api.github.com/users/{username}")
        return True
    except Exception as e:
        if hasattr(e, "status") and e.status == 404:
            return False
        raise