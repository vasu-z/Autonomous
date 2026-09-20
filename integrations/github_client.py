import httpx
from typing import Dict, Any, Optional
from config import settings

class GitHubClient:
    """
    GitHub Integration Module: Communicates with GitHub API for issue fetching,
    branch creation, commit management, and Pull Request submission.
    Gracefully falls back to simulated PR generation if no token is configured.
    """

    def __init__(self, token: str = None):
        self.token = token or settings.GITHUB_TOKEN
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Autonomous-DevOps-Agent"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def fetch_issue(self, repo: str, issue_number: int) -> Dict[str, Any]:
        """Fetches issue title and body from GitHub."""
        if not self.token:
            return {
                "title": f"Simulated Issue #{issue_number}",
                "body": "Fix authentication bug and add rate limiting to API endpoints.",
                "url": f"https://github.com/{repo}/issues/{issue_number}"
            }

        url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "title": data.get("title", ""),
                        "body": data.get("body", ""),
                        "url": data.get("html_url", "")
                    }
        except Exception:
            pass

        return {
            "title": f"Issue #{issue_number}",
            "body": "Issue details retrieved via fallback.",
            "url": f"https://github.com/{repo}/issues/{issue_number}"
        }

    def create_pull_request(
        self, repo: str, branch: str, base: str, title: str, body: str
    ) -> Dict[str, Any]:
        """Creates a Pull Request on GitHub."""
        if not self.token or not repo:
            # Simulated Pull Request
            pr_num = 42
            pr_url = f"https://github.com/{repo or 'autonomous-dev/repo'}/pull/{pr_num}"
            return {
                "success": True,
                "pr_number": pr_num,
                "html_url": pr_url,
                "status": "OPEN",
                "simulated": True
            }

        url = f"https://api.github.com/repos/{repo}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": branch,
            "base": base
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, json=payload, headers=self.headers)
                if res.status_code in (200, 201):
                    data = res.json()
                    return {
                        "success": True,
                        "pr_number": data.get("number"),
                        "html_url": data.get("html_url"),
                        "status": "OPEN",
                        "simulated": False
                    }
                else:
                    return {
                        "success": False,
                        "error": f"GitHub API returned status {res.status_code}: {res.text}"
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}
