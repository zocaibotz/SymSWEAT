import os
import re
import json
import subprocess
from typing import Dict, Any, Optional


class GitHubBootstrapTool:
    def __init__(self, owner: str = None):
        self.owner = owner or os.getenv("SWEAT_GITHUB_OWNER", "zocaibotz")
        self._secret_blocklist = {
            ".env",
            ".env.local",
            ".env.production",
            ".env.development",
            ".env.test",
            "*.pem",
            "*.key",
            "id_rsa",
            "id_ed25519",
        }

    @staticmethod
    def _run(cmd: list[str], cwd: str) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

    @staticmethod
    def _slugify(name: str) -> str:
        s = (name or "project").strip().lower()
        s = re.sub(r"[^a-z0-9._-]+", "-", s)
        s = re.sub(r"-+", "-", s).strip("-")
        return s or "project"

    def _write_repo_policy_files(self, cwd: str = ".") -> None:
        os.makedirs(os.path.join(cwd, ".github"), exist_ok=True)

        codeowners = """# Default code owners\n* @zocaibotz\n"""
        pr_template = """## Summary\n- What changed?\n\n## Validation\n- [ ] Unit tests\n- [ ] Integration tests\n- [ ] E2E/Playwright checks\n\n## Risk\n- [ ] Low\n- [ ] Medium\n- [ ] High\n"""

        with open(os.path.join(cwd, ".github", "CODEOWNERS"), "w", encoding="utf-8") as f:
            f.write(codeowners)
        with open(os.path.join(cwd, ".github", "pull_request_template.md"), "w", encoding="utf-8") as f:
            f.write(pr_template)

        # PR auto-label bootstrap
        with open(os.path.join(cwd, ".github", "labeler.yml"), "w", encoding="utf-8") as f:
            f.write("documentation:\n  - '**/*.md'\npython:\n  - '**/*.py'\nci:\n  - '.github/workflows/*'\n")

        os.makedirs(os.path.join(cwd, ".github", "workflows"), exist_ok=True)
        with open(os.path.join(cwd, ".github", "workflows", "pr-labeler.yml"), "w", encoding="utf-8") as f:
            f.write(
                "name: PR Labeler\n"
                "on:\n  pull_request_target:\n    types: [opened, synchronize, reopened]\n"
                "jobs:\n"
                "  label:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/labeler@v5\n"
                "        with:\n"
                "          repo-token: ${{ secrets.GITHUB_TOKEN }}\n"
                "          configuration-path: .github/labeler.yml\n"
            )

    def _validate_policy_files(self, cwd: str = ".") -> Dict[str, Any]:
        required = [
            ".github/CODEOWNERS",
            ".github/pull_request_template.md",
            ".github/labeler.yml",
            ".github/workflows/pr-labeler.yml",
            ".gitignore",
        ]
        missing = [p for p in required if not os.path.exists(os.path.join(cwd, p))]
        return {"success": len(missing) == 0, "missing": missing}

    def _ensure_gitignore(self, cwd: str = ".") -> None:
        path = os.path.join(cwd, ".gitignore")
        required = [
            "# SWEAT mandatory secrets guard",
            ".env",
            ".env.*",
            "!.env.example",
            "*.pem",
            "*.key",
            "id_rsa",
            "id_ed25519",
            ".venv/",
            "venv/",
            "node_modules/",
            "__pycache__/",
            ".DS_Store",
        ]
        existing = ""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = f.read()

        to_add = [line for line in required if line not in existing]
        if to_add:
            with open(path, "a", encoding="utf-8") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write("\n".join(to_add) + "\n")

    def _untrack_blocked_secret_files(self, cwd: str = ".") -> None:
        tracked = self._run(["git", "ls-files"], cwd)
        if tracked.returncode != 0:
            return
        files = [x.strip() for x in tracked.stdout.splitlines() if x.strip()]

        def _matches(name: str) -> bool:
            if name in {".env", ".env.local", ".env.production", ".env.development", ".env.test", "id_rsa", "id_ed25519"}:
                return True
            if name.startswith(".env.") and name != ".env.example":
                return True
            if name.endswith(".pem") or name.endswith(".key"):
                return True
            return False

        blocked = [f for f in files if _matches(f)]
        for f in blocked:
            self._run(["git", "rm", "--cached", "-f", f], cwd)

    def _apply_branch_protection(self, repo: str, branch: str = "master", cwd: str = ".") -> Dict[str, Any]:
        payload = {
            "required_status_checks": {
                "strict": True,
                "contexts": ["unit", "integration", "e2e_playwright"],
            },
            "enforce_admins": False,
            "required_pull_request_reviews": {
                "required_approving_review_count": 1,
                "dismiss_stale_reviews": True,
                "require_code_owner_reviews": False,
            },
            "restrictions": None,
            "required_linear_history": False,
            "allow_force_pushes": False,
            "allow_deletions": False,
        }

        cmd = [
            "gh", "api",
            f"repos/{repo}/branches/{branch}/protection",
            "--method", "PUT",
            "--input", "-",
            "-H", "Accept: application/vnd.github+json",
        ]
        proc = subprocess.run(cmd, cwd=cwd, input=json.dumps(payload), capture_output=True, text=True)
        if proc.returncode != 0:
            return {"success": False, "error": proc.stderr or proc.stdout}
        return {"success": True}

    def bootstrap_repo(
        self,
        project_name: str,
        cwd: str = ".",
        private: bool = True,
        description: str = "",
    ) -> Dict[str, Any]:
        # Strict factory policy: repositories must be private.
        if not private:
            return {"success": False, "error": "Factory policy violation: repositories must be private."}
        slug = self._slugify(project_name)
        repo = f"{self.owner}/{slug}"

        # Ensure git repo
        if not os.path.exists(os.path.join(cwd, ".git")):
            r = self._run(["git", "init"], cwd)
            if r.returncode != 0:
                return {"success": False, "error": f"git init failed: {r.stderr}"}

        # Bootstrap repository safety/policy files
        self._ensure_gitignore(cwd)
        self._write_repo_policy_files(cwd)
        self._untrack_blocked_secret_files(cwd)

        # Ensure at least one commit (if none)
        head = self._run(["git", "rev-parse", "--verify", "HEAD"], cwd)
        if head.returncode != 0:
            self._run(["git", "add", "."], cwd)
            # Safety re-check after add to avoid secret commits
            self._untrack_blocked_secret_files(cwd)
            self._run(["git", "commit", "-m", "chore: initial commit"], cwd)

        policy_check = self._validate_policy_files(cwd)
        if not policy_check.get("success"):
            return {"success": False, "error": f"Policy bootstrap incomplete, missing: {policy_check.get('missing')}"}

        # Check remote
        remote_get = self._run(["git", "remote", "get-url", "origin"], cwd)
        if remote_get.returncode == 0:
            remote_url = remote_get.stdout.strip()
            protection = self._apply_branch_protection(repo=repo, branch="master", cwd=cwd)
            bypass = os.getenv("SWEAT_ALLOW_BRANCH_PROTECTION_BYPASS", "false").lower() in {"1", "true", "yes", "on"}
            if not protection.get("success") and not bypass:
                return {
                    "success": False,
                    "error": f"Branch protection enforcement failed: {protection.get('error')}",
                    "repo": repo,
                    "url": remote_url,
                }
            return {
                "success": True,
                "repo": repo,
                "url": remote_url,
                "created": False,
                "policy_files_bootstrapped": True,
                "branch_protection_applied": protection.get("success", False),
                "branch_protection_error": protection.get("error"),
                "branch_protection_bypassed": (not protection.get("success") and bypass),
            }

        # Create GitHub repo and push
        create_cmd = [
            "gh", "repo", "create", repo,
            "--source", ".",
            "--remote", "origin",
            "--push",
        ]
        create_cmd.append("--private" if private else "--public")
        if description:
            create_cmd.extend(["--description", description])

        created = self._run(create_cmd, cwd)
        if created.returncode != 0:
            return {"success": False, "error": f"gh repo create failed: {created.stderr or created.stdout}"}

        remote_get = self._run(["git", "remote", "get-url", "origin"], cwd)
        remote_url = remote_get.stdout.strip() if remote_get.returncode == 0 else f"https://github.com/{repo}"
        protection = self._apply_branch_protection(repo=repo, branch="master", cwd=cwd)
        bypass = os.getenv("SWEAT_ALLOW_BRANCH_PROTECTION_BYPASS", "false").lower() in {"1", "true", "yes", "on"}
        if not protection.get("success") and not bypass:
            return {
                "success": False,
                "error": f"Branch protection enforcement failed: {protection.get('error')}",
                "repo": repo,
                "url": remote_url,
            }
        return {
            "success": True,
            "repo": repo,
            "url": remote_url,
            "created": True,
            "policy_files_bootstrapped": True,
            "branch_protection_applied": protection.get("success", False),
            "branch_protection_error": protection.get("error"),
            "branch_protection_bypassed": (not protection.get("success") and bypass),
        }


_github_bootstrap = GitHubBootstrapTool()


def get_github_bootstrap_tool() -> GitHubBootstrapTool:
    return _github_bootstrap
