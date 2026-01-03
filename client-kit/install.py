#!/usr/bin/env python3
"""
Error Observability Client-Kit Installer
=========================================

Cross-platform installer for integrating Sentry SDK with your applications.
Automatically detects project language and applies minimal, non-destructive changes.

Usage:
    python install.py                    # Interactive mode
    python install.py --dsn <DSN>        # With DSN parameter
    python install.py --update-dsn       # Update DSN only
    python install.py --update-client    # Update client code from templates

API Mode (automatic project/team creation):
    python install.py --api-key <KEY> --api-url <URL> --team <TEAM> --project <PROJECT>

Requirements:
    Python 3.7+
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# CONFIGURATION
# =============================================================================

class Language(Enum):
    PYTHON = "python"
    NODEJS = "nodejs"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    DOTNET = "dotnet"
    GO = "go"
    PHP = "php"
    RUBY = "ruby"
    UNKNOWN = "unknown"


@dataclass
class ProjectInfo:
    language: Language
    framework: Optional[str]
    project_name: str
    project_root: Path
    package_manager: Optional[str]
    config_files: List[Path]


@dataclass
class SentryConfig:
    dsn: str
    environment: str = "production"
    release: Optional[str] = None


# =============================================================================
# BUGSINK API CLIENT
# =============================================================================

class BugsinkAPI:
    """Client for Bugsink API v0 to manage teams and projects."""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.base_path = "/api/canonical/0"

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Tuple[int, Any]:
        """Make an API request."""
        url = f"{self.api_url}{self.base_path}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        body = json.dumps(data).encode("utf-8") if data else None

        try:
            request = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(request, timeout=30) as response:
                response_body = response.read().decode("utf-8")
                return response.status, json.loads(response_body) if response_body else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            try:
                error_data = json.loads(error_body) if error_body else {}
            except json.JSONDecodeError:
                error_data = {"detail": error_body}
            return e.code, error_data
        except urllib.error.URLError as e:
            return 0, {"detail": str(e.reason)}
        except Exception as e:
            return 0, {"detail": str(e)}

    def test_connection(self) -> bool:
        """Test if the API connection works."""
        status, _ = self._request("GET", "/teams/")
        return status == 200

    def list_teams(self) -> List[Dict]:
        """List all teams."""
        status, data = self._request("GET", "/teams/")
        if status == 200:
            return data.get("results", [])
        return []

    def get_team_by_name(self, name: str) -> Optional[Dict]:
        """Find a team by name."""
        teams = self.list_teams()
        for team in teams:
            if team.get("name", "").lower() == name.lower():
                return team
        return None

    def create_team(self, name: str, visibility: str = "joinable") -> Optional[Dict]:
        """Create a new team."""
        status, data = self._request("POST", "/teams/", {
            "name": name,
            "visibility": visibility
        })
        if status == 201:
            return data
        print(f"  Error creating team: {data}")
        return None

    def get_or_create_team(self, name: str) -> Optional[Dict]:
        """Get existing team or create a new one."""
        team = self.get_team_by_name(name)
        if team:
            print(f"  Found existing team: {name}")
            return team

        print(f"  Creating team: {name}")
        return self.create_team(name)

    def list_projects(self, team_id: Optional[str] = None) -> List[Dict]:
        """List all projects, optionally filtered by team."""
        endpoint = "/projects/"
        if team_id:
            endpoint += f"?team={team_id}"

        status, data = self._request("GET", endpoint)
        if status == 200:
            return data.get("results", [])
        return []

    def get_project_by_name(self, name: str, team_id: Optional[str] = None) -> Optional[Dict]:
        """Find a project by name."""
        projects = self.list_projects(team_id)
        for project in projects:
            if project.get("name", "").lower() == name.lower():
                return project
        return None

    def get_project_details(self, project_id: int) -> Optional[Dict]:
        """Get project details including DSN."""
        status, data = self._request("GET", f"/projects/{project_id}/")
        if status == 200:
            return data
        return None

    def create_project(self, team_id: str, name: str, visibility: str = "team_members") -> Optional[Dict]:
        """Create a new project."""
        status, data = self._request("POST", "/projects/", {
            "team": team_id,
            "name": name,
            "visibility": visibility
        })
        if status == 201:
            # Need to get project details to get the DSN
            project_id = data.get("id")
            if project_id:
                return self.get_project_details(project_id)
            return data
        print(f"  Error creating project: {data}")
        return None

    def get_or_create_project(self, team_id: str, name: str) -> Optional[Dict]:
        """Get existing project or create a new one, returns project with DSN."""
        project = self.get_project_by_name(name, team_id)
        if project:
            print(f"  Found existing project: {name}")
            # Get full details including DSN
            return self.get_project_details(project.get("id"))

        print(f"  Creating project: {name}")
        return self.create_project(team_id, name)


# =============================================================================
# LANGUAGE DETECTION
# =============================================================================

class LanguageDetector:
    """Detects project language and framework based on files present."""

    DETECTION_PATTERNS: Dict[Language, List[Tuple[str, Optional[str]]]] = {
        Language.PYTHON: [
            ("requirements.txt", None),
            ("pyproject.toml", None),
            ("setup.py", None),
            ("Pipfile", None),
            ("manage.py", "django"),
            ("app.py", "flask"),
            ("main.py", None),
        ],
        Language.NODEJS: [
            ("package.json", None),
        ],
        Language.TYPESCRIPT: [
            ("tsconfig.json", None),
        ],
        Language.JAVA: [
            ("pom.xml", "maven"),
            ("build.gradle", "gradle"),
            ("build.gradle.kts", "gradle"),
        ],
        Language.DOTNET: [
            ("*.csproj", None),
            ("*.fsproj", None),
            ("*.sln", None),
        ],
        Language.GO: [
            ("go.mod", None),
            ("go.sum", None),
        ],
        Language.PHP: [
            ("composer.json", None),
        ],
        Language.RUBY: [
            ("Gemfile", None),
            ("*.gemspec", None),
        ],
    }

    FRAMEWORK_DETECTION = {
        Language.PYTHON: {
            "django": ["manage.py", "settings.py"],
            "flask": ["app.py"],
            "fastapi": ["main.py"],
        },
        Language.NODEJS: {
            "express": ["package.json"],  # Check package.json content
            "nestjs": ["nest-cli.json"],
            "nextjs": ["next.config.js", "next.config.mjs"],
        },
    }

    @classmethod
    def detect(cls, project_root: Path) -> ProjectInfo:
        """Detect project language and framework."""
        detected_language = Language.UNKNOWN
        detected_framework = None
        config_files = []
        package_manager = None

        # Check each language pattern
        for language, patterns in cls.DETECTION_PATTERNS.items():
            for pattern, framework in patterns:
                if "*" in pattern:
                    matches = list(project_root.glob(pattern))
                    if matches:
                        detected_language = language
                        config_files.extend(matches)
                        if framework:
                            detected_framework = framework
                        break
                else:
                    file_path = project_root / pattern
                    if file_path.exists():
                        detected_language = language
                        config_files.append(file_path)
                        if framework:
                            detected_framework = framework
                        break

            if detected_language != Language.UNKNOWN:
                break

        # TypeScript detection (refine from nodejs)
        if detected_language == Language.NODEJS:
            if (project_root / "tsconfig.json").exists():
                detected_language = Language.TYPESCRIPT
                config_files.append(project_root / "tsconfig.json")

        # Detect package manager
        package_manager = cls._detect_package_manager(project_root, detected_language)

        # Detect framework from package.json for Node.js
        if detected_language in (Language.NODEJS, Language.TYPESCRIPT):
            detected_framework = cls._detect_node_framework(project_root)

        # Get project name from folder
        project_name = project_root.name

        return ProjectInfo(
            language=detected_language,
            framework=detected_framework,
            project_name=project_name,
            project_root=project_root,
            package_manager=package_manager,
            config_files=config_files,
        )

    @classmethod
    def _detect_package_manager(cls, root: Path, language: Language) -> Optional[str]:
        """Detect the package manager for the project."""
        managers = {
            Language.PYTHON: [
                ("poetry.lock", "poetry"),
                ("Pipfile.lock", "pipenv"),
                ("requirements.txt", "pip"),
            ],
            Language.NODEJS: [
                ("pnpm-lock.yaml", "pnpm"),
                ("yarn.lock", "yarn"),
                ("package-lock.json", "npm"),
            ],
            Language.TYPESCRIPT: [
                ("pnpm-lock.yaml", "pnpm"),
                ("yarn.lock", "yarn"),
                ("package-lock.json", "npm"),
            ],
        }

        for lock_file, manager in managers.get(language, []):
            if (root / lock_file).exists():
                return manager

        return None

    @classmethod
    def _detect_node_framework(cls, root: Path) -> Optional[str]:
        """Detect Node.js framework from package.json."""
        package_json = root / "package.json"
        if not package_json.exists():
            return None

        try:
            with open(package_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

            if "@nestjs/core" in deps:
                return "nestjs"
            if "next" in deps:
                return "nextjs"
            if "express" in deps:
                return "express"
            if "fastify" in deps:
                return "fastify"
            if "koa" in deps:
                return "koa"
        except (json.JSONDecodeError, IOError):
            pass

        return None


# =============================================================================
# TEMPLATE MANAGER
# =============================================================================

class TemplateManager:
    """Manages templates for different languages."""

    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir

    def get_template_path(self, language: Language) -> Path:
        """Get the template directory for a language."""
        return self.templates_dir / language.value

    def get_template_files(self, language: Language) -> List[Path]:
        """Get all template files for a language."""
        template_path = self.get_template_path(language)
        if not template_path.exists():
            return []
        return list(template_path.glob("**/*"))

    def render_template(self, template_path: Path, config: SentryConfig) -> str:
        """Render a template with the given configuration."""
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace placeholders
        replacements = {
            "{{DSN}}": config.dsn,
            "{{ENVIRONMENT}}": config.environment,
            "{{RELEASE}}": config.release or "",
            "${SENTRY_DSN}": config.dsn,
        }

        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)

        return content


# =============================================================================
# INSTALLERS
# =============================================================================

class BaseInstaller:
    """Base class for language-specific installers."""

    def __init__(self, project: ProjectInfo, config: SentryConfig, templates: TemplateManager):
        self.project = project
        self.config = config
        self.templates = templates

    def install(self) -> bool:
        """Run the installation process."""
        raise NotImplementedError

    def update_dsn(self) -> bool:
        """Update only the DSN in existing configuration."""
        raise NotImplementedError

    def update_client(self) -> bool:
        """Update client code from templates."""
        raise NotImplementedError

    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> bool:
        """Run a shell command."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project.project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"  Warning: {' '.join(cmd)} failed: {result.stderr}")
                return False
            return True
        except Exception as e:
            print(f"  Error running command: {e}")
            return False

    def _copy_template(self, template_name: str, dest_path: Path) -> bool:
        """Copy a template file to the destination."""
        template_path = self.templates.get_template_path(self.project.language) / template_name
        if not template_path.exists():
            print(f"  Template not found: {template_path}")
            return False

        content = self.templates.render_template(template_path, self.config)

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"  Created: {dest_path.relative_to(self.project.project_root)}")
        return True

    def _update_env_file(self, env_var: str = "SENTRY_DSN") -> bool:
        """Add or update DSN in .env file."""
        env_file = self.project.project_root / ".env"
        env_example = self.project.project_root / ".env.example"

        # Update .env
        self._update_env_var(env_file, env_var, self.config.dsn)

        # Also update .env.example with placeholder
        if env_example.exists():
            self._update_env_var(env_example, env_var, "https://your-key@your-host/1", only_if_missing=True)

        return True

    def _update_env_var(self, env_file: Path, var_name: str, value: str, only_if_missing: bool = False):
        """Update or add an environment variable in a .env file."""
        lines = []
        found = False

        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if line.strip().startswith(f"{var_name}="):
                    if not only_if_missing:
                        lines[i] = f"{var_name}={value}\n"
                    found = True
                    break

        if not found:
            if lines and not lines[-1].endswith("\n"):
                lines.append("\n")
            lines.append(f"\n# Error Observability\n{var_name}={value}\n")

        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"  Updated: {env_file.name}")


class PythonInstaller(BaseInstaller):
    """Installer for Python projects."""

    def install(self) -> bool:
        print("\n  Installing Sentry SDK for Python...")

        # Install package
        if self.project.package_manager == "poetry":
            self._run_command(["poetry", "add", "sentry-sdk"])
        elif self.project.package_manager == "pipenv":
            self._run_command(["pipenv", "install", "sentry-sdk"])
        else:
            self._run_command([sys.executable, "-m", "pip", "install", "sentry-sdk"])
            # Add to requirements.txt if exists
            req_file = self.project.project_root / "requirements.txt"
            if req_file.exists():
                with open(req_file, "a", encoding="utf-8") as f:
                    f.write("\nsentry-sdk>=2.0.0\n")
                print("  Added sentry-sdk to requirements.txt")

        # Copy template files
        self._copy_template("sentry_config.py", self.project.project_root / "sentry_config.py")

        # Update .env
        self._update_env_file()

        print("\n  Integration complete!")
        print("  Add this to your application entry point:")
        print("  ─────────────────────────────────────────")
        print("  from sentry_config import init_sentry")
        print("  init_sentry()")
        print("  ─────────────────────────────────────────")

        return True

    def update_dsn(self) -> bool:
        self._update_env_file()

        # Also update sentry_config.py if it has hardcoded DSN
        config_file = self.project.project_root / "sentry_config.py"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace DSN pattern
            content = re.sub(
                r'dsn\s*=\s*["\'][^"\']+["\']',
                f'dsn=os.getenv("SENTRY_DSN", "{self.config.dsn}")',
                content
            )

            with open(config_file, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"  Updated: sentry_config.py")

        return True

    def update_client(self) -> bool:
        self._copy_template("sentry_config.py", self.project.project_root / "sentry_config.py")
        return True


class NodeInstaller(BaseInstaller):
    """Installer for Node.js/TypeScript projects."""

    def install(self) -> bool:
        lang_name = "TypeScript" if self.project.language == Language.TYPESCRIPT else "Node.js"
        print(f"\n  Installing Sentry SDK for {lang_name}...")

        # Install packages
        packages = ["@sentry/node"]

        if self.project.package_manager == "pnpm":
            self._run_command(["pnpm", "add"] + packages)
        elif self.project.package_manager == "yarn":
            self._run_command(["yarn", "add"] + packages)
        else:
            self._run_command(["npm", "install", "--save"] + packages)

        # Copy template files
        if self.project.language == Language.TYPESCRIPT:
            self._copy_template("sentry.config.ts", self.project.project_root / "src" / "sentry.config.ts")
        else:
            self._copy_template("sentry.config.js", self.project.project_root / "sentry.config.js")

        # Update .env
        self._update_env_file()

        print("\n  Integration complete!")
        print("  Add this at the TOP of your entry file:")
        print("  ─────────────────────────────────────────")
        if self.project.language == Language.TYPESCRIPT:
            print('  import "./sentry.config";')
        else:
            print('  require("./sentry.config");')
        print("  ─────────────────────────────────────────")

        return True

    def update_dsn(self) -> bool:
        self._update_env_file()
        return True

    def update_client(self) -> bool:
        if self.project.language == Language.TYPESCRIPT:
            self._copy_template("sentry.config.ts", self.project.project_root / "src" / "sentry.config.ts")
        else:
            self._copy_template("sentry.config.js", self.project.project_root / "sentry.config.js")
        return True


class DotNetInstaller(BaseInstaller):
    """Installer for .NET projects."""

    def install(self) -> bool:
        print("\n  Installing Sentry SDK for .NET...")

        # Find .csproj file
        csproj_files = list(self.project.project_root.glob("**/*.csproj"))
        if csproj_files:
            for csproj in csproj_files:
                self._run_command(["dotnet", "add", str(csproj), "package", "Sentry"])

        # Copy template
        self._copy_template("SentryConfig.cs", self.project.project_root / "SentryConfig.cs")

        # Update environment
        self._update_env_file()

        print("\n  Integration complete!")
        print("  Add this to your Program.cs:")
        print("  ─────────────────────────────────────────")
        print("  builder.WebHost.UseSentry();")
        print("  // Or for console apps:")
        print("  SentryConfig.Init();")
        print("  ─────────────────────────────────────────")

        return True

    def update_dsn(self) -> bool:
        self._update_env_file()
        return True

    def update_client(self) -> bool:
        self._copy_template("SentryConfig.cs", self.project.project_root / "SentryConfig.cs")
        return True


class GoInstaller(BaseInstaller):
    """Installer for Go projects."""

    def install(self) -> bool:
        print("\n  Installing Sentry SDK for Go...")

        self._run_command(["go", "get", "github.com/getsentry/sentry-go"])

        self._copy_template("sentry.go", self.project.project_root / "pkg" / "sentry" / "sentry.go")

        self._update_env_file()

        print("\n  Integration complete!")
        print("  Add this to your main.go:")
        print("  ─────────────────────────────────────────")
        print('  import "your-module/pkg/sentry"')
        print("  ")
        print("  func main() {")
        print("      sentry.Init()")
        print("      defer sentry.Flush()")
        print("      // ...")
        print("  }")
        print("  ─────────────────────────────────────────")

        return True

    def update_dsn(self) -> bool:
        self._update_env_file()
        return True

    def update_client(self) -> bool:
        self._copy_template("sentry.go", self.project.project_root / "pkg" / "sentry" / "sentry.go")
        return True


class PHPInstaller(BaseInstaller):
    """Installer for PHP projects."""

    def install(self) -> bool:
        print("\n  Installing Sentry SDK for PHP...")

        self._run_command(["composer", "require", "sentry/sentry"])

        self._copy_template("sentry.php", self.project.project_root / "config" / "sentry.php")

        self._update_env_file()

        print("\n  Integration complete!")
        print("  Add this to your bootstrap/entry file:")
        print("  ─────────────────────────────────────────")
        print("  require_once 'config/sentry.php';")
        print("  ─────────────────────────────────────────")

        return True

    def update_dsn(self) -> bool:
        self._update_env_file()
        return True

    def update_client(self) -> bool:
        self._copy_template("sentry.php", self.project.project_root / "config" / "sentry.php")
        return True


class RubyInstaller(BaseInstaller):
    """Installer for Ruby projects."""

    def install(self) -> bool:
        print("\n  Installing Sentry SDK for Ruby...")

        # Add to Gemfile
        gemfile = self.project.project_root / "Gemfile"
        if gemfile.exists():
            with open(gemfile, "a", encoding="utf-8") as f:
                f.write('\n\n# Error Observability\ngem "sentry-ruby"\n')
            print("  Added sentry-ruby to Gemfile")
            self._run_command(["bundle", "install"])

        self._copy_template("sentry.rb", self.project.project_root / "config" / "initializers" / "sentry.rb")

        self._update_env_file()

        print("\n  Integration complete!")
        print("  For Rails: The initializer will load automatically.")
        print("  For other apps, add:")
        print("  ─────────────────────────────────────────")
        print("  require_relative 'config/initializers/sentry'")
        print("  ─────────────────────────────────────────")

        return True

    def update_dsn(self) -> bool:
        self._update_env_file()
        return True

    def update_client(self) -> bool:
        self._copy_template("sentry.rb", self.project.project_root / "config" / "initializers" / "sentry.rb")
        return True


class JavaInstaller(BaseInstaller):
    """Installer for Java projects."""

    def install(self) -> bool:
        print("\n  Installing Sentry SDK for Java...")

        # Detect build tool and add dependency
        pom = self.project.project_root / "pom.xml"
        gradle = self.project.project_root / "build.gradle"
        gradle_kts = self.project.project_root / "build.gradle.kts"

        if pom.exists():
            print("  Add this to your pom.xml <dependencies>:")
            print("  ─────────────────────────────────────────")
            print("  <dependency>")
            print("      <groupId>io.sentry</groupId>")
            print("      <artifactId>sentry</artifactId>")
            print("      <version>7.0.0</version>")
            print("  </dependency>")
            print("  ─────────────────────────────────────────")
        elif gradle.exists() or gradle_kts.exists():
            print("  Add this to your build.gradle dependencies:")
            print("  ─────────────────────────────────────────")
            print("  implementation 'io.sentry:sentry:7.0.0'")
            print("  ─────────────────────────────────────────")

        self._copy_template("SentryConfig.java",
                           self.project.project_root / "src" / "main" / "java" / "SentryConfig.java")

        self._update_env_file()

        print("\n  Call SentryConfig.init() in your main method.")

        return True

    def update_dsn(self) -> bool:
        self._update_env_file()
        return True

    def update_client(self) -> bool:
        self._copy_template("SentryConfig.java",
                           self.project.project_root / "src" / "main" / "java" / "SentryConfig.java")
        return True


# =============================================================================
# MAIN INSTALLER
# =============================================================================

class ClientKitInstaller:
    """Main installer orchestrator."""

    INSTALLERS = {
        Language.PYTHON: PythonInstaller,
        Language.NODEJS: NodeInstaller,
        Language.TYPESCRIPT: NodeInstaller,
        Language.JAVA: JavaInstaller,
        Language.DOTNET: DotNetInstaller,
        Language.GO: GoInstaller,
        Language.PHP: PHPInstaller,
        Language.RUBY: RubyInstaller,
    }

    def __init__(self):
        # Determine paths
        self.script_dir = Path(__file__).parent.resolve()
        self.templates_dir = self.script_dir / "templates"
        self.project_root = Path.cwd()

        self.templates = TemplateManager(self.templates_dir)
        self.project: Optional[ProjectInfo] = None
        self.config: Optional[SentryConfig] = None
        self.api: Optional[BugsinkAPI] = None

    def run(self, args: argparse.Namespace):
        """Run the installer based on arguments."""
        print("=" * 60)
        print("  Error Observability - Client Kit Installer")
        print("=" * 60)

        # Detect project
        self.project = LanguageDetector.detect(self.project_root)

        print(f"\n  Project: {self.project.project_name}")
        print(f"  Language: {self.project.language.value}")
        if self.project.framework:
            print(f"  Framework: {self.project.framework}")
        if self.project.package_manager:
            print(f"  Package Manager: {self.project.package_manager}")

        if self.project.language == Language.UNKNOWN:
            print("\n  Error: Could not detect project language.")
            print("  Supported: Python, Node.js, TypeScript, Java, .NET, Go, PHP, Ruby")
            return 1

        # Initialize API client if credentials provided
        api_key = args.api_key or os.getenv("BUGSINK_API_KEY")
        api_url = args.api_url or os.getenv("BUGSINK_API_URL")

        if api_key and api_url:
            self.api = BugsinkAPI(api_url, api_key)
            if not self.api.test_connection():
                print("\n  Warning: Could not connect to Bugsink API.")
                print("  Falling back to manual DSN mode.")
                self.api = None
            else:
                print(f"\n  Connected to Bugsink API: {api_url}")

        # Get DSN - either via API or manually
        dsn = args.dsn or os.getenv("SENTRY_DSN")

        # If API is available and no DSN provided, use API mode
        if self.api and not dsn and not args.update_client:
            dsn = self._get_dsn_via_api(args)

        # Fallback to manual DSN prompt if needed
        if not dsn and not args.update_client:
            dsn = self._prompt_dsn()

        if dsn:
            self.config = SentryConfig(
                dsn=dsn,
                environment=args.environment or "production",
                release=args.release,
            )

        # Determine action
        if args.update_dsn:
            return self._update_dsn()
        elif args.update_client:
            return self._update_client()
        else:
            return self._interactive_menu()

    def _get_dsn_via_api(self, args: argparse.Namespace) -> Optional[str]:
        """Get DSN via Bugsink API by creating/finding team and project."""
        print("\n  API Mode: Automatic project setup")
        print("  ─────────────────────────────────────────")

        # Get team name - from args, env, or prompt
        team_name = args.team or os.getenv("BUGSINK_TEAM")
        if not team_name:
            # Show available teams
            teams = self.api.list_teams()
            if teams:
                print("\n  Available teams:")
                for i, team in enumerate(teams, 1):
                    print(f"    {i}. {team.get('name')}")
                print(f"    {len(teams) + 1}. Create new team")
                print("")

                choice = input("  Select team number or enter new team name: ").strip()

                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(teams):
                        team_name = teams[idx].get("name")
                    elif idx == len(teams):
                        team_name = input("  Enter new team name: ").strip()
                else:
                    team_name = choice
            else:
                team_name = input("  Enter team name: ").strip()

        if not team_name:
            print("  Error: Team name is required.")
            return None

        # Get or create team
        team = self.api.get_or_create_team(team_name)
        if not team:
            print("  Error: Could not get or create team.")
            return None

        team_id = team.get("id")

        # Get project name - from args, env, or use detected project name
        project_name = args.project or os.getenv("BUGSINK_PROJECT") or self.project.project_name

        # Show available projects in team
        projects = self.api.list_projects(team_id)
        if projects and not args.project:
            print(f"\n  Existing projects in team '{team_name}':")
            for i, proj in enumerate(projects, 1):
                print(f"    {i}. {proj.get('name')}")
            print(f"    {len(projects) + 1}. Create new project")
            print("")

            default_msg = f" (default: {project_name})" if project_name else ""
            choice = input(f"  Select project number or enter new name{default_msg}: ").strip()

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(projects):
                    project_name = projects[idx].get("name")
                elif idx == len(projects):
                    new_name = input(f"  Enter new project name [{project_name}]: ").strip()
                    if new_name:
                        project_name = new_name
            elif choice:
                project_name = choice

        if not project_name:
            print("  Error: Project name is required.")
            return None

        # Get or create project
        project = self.api.get_or_create_project(team_id, project_name)
        if not project:
            print("  Error: Could not get or create project.")
            return None

        dsn = project.get("dsn")
        if dsn:
            print("\n  DSN retrieved successfully!")
            print(f"  Team: {team_name}")
            print(f"  Project: {project_name}")
            return dsn

        print("  Error: Could not retrieve DSN from project.")
        return None

    def _prompt_dsn(self) -> str:
        """Prompt user for DSN."""
        print("\n  DSN not found in environment.")
        print("  Get your DSN from: Project Settings > Client Keys")
        print("")
        dsn = input("  Enter DSN (or press Enter to skip): ").strip()
        return dsn

    def _interactive_menu(self) -> int:
        """Show interactive menu."""
        print("\n  What would you like to do?")
        print("  ─────────────────────────────────────────")
        print("  1. Set up new integration")
        print("  2. Update DSN only")
        print("  3. Update client code from templates")
        print("  4. Exit")
        print("")

        choice = input("  Enter choice [1-4]: ").strip()

        if choice == "1":
            return self._install()
        elif choice == "2":
            return self._update_dsn()
        elif choice == "3":
            return self._update_client()
        else:
            print("  Exiting.")
            return 0

    def _get_installer(self) -> Optional[BaseInstaller]:
        """Get the appropriate installer for the detected language."""
        installer_class = self.INSTALLERS.get(self.project.language)
        if not installer_class:
            print(f"\n  Error: No installer available for {self.project.language.value}")
            return None

        return installer_class(self.project, self.config, self.templates)

    def _install(self) -> int:
        """Run full installation."""
        if not self.config or not self.config.dsn:
            print("\n  Error: DSN is required for installation.")
            return 1

        installer = self._get_installer()
        if not installer:
            return 1

        success = installer.install()
        return 0 if success else 1

    def _update_dsn(self) -> int:
        """Update DSN only."""
        if not self.config or not self.config.dsn:
            print("\n  Error: DSN is required.")
            return 1

        installer = self._get_installer()
        if not installer:
            return 1

        print("\n  Updating DSN...")
        success = installer.update_dsn()

        if success:
            print("\n  DSN updated successfully!")

        return 0 if success else 1

    def _update_client(self) -> int:
        """Update client code from templates."""
        # For update, we need to read existing DSN
        if not self.config:
            dsn = os.getenv("SENTRY_DSN", "")
            env_file = self.project.project_root / ".env"
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("SENTRY_DSN="):
                            dsn = line.split("=", 1)[1].strip()
                            break

            self.config = SentryConfig(dsn=dsn)

        installer = self._get_installer()
        if not installer:
            return 1

        print("\n  Updating client code from templates...")
        success = installer.update_client()

        if success:
            print("\n  Client code updated successfully!")

        return 0 if success else 1


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Error Observability Client Kit - SDK Integration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install.py                          # Interactive mode
  python install.py --dsn "https://..."      # Install with DSN
  python install.py --update-dsn --dsn "..." # Update DSN only
  python install.py --update-client          # Update client code

API Mode (automatic project creation):
  python install.py --api-key <KEY> --api-url <URL>
  python install.py --api-key <KEY> --api-url <URL> --team "MyTeam" --project "MyApp"

Environment Variables:
  SENTRY_DSN         - Sentry/Bugsink DSN
  SENTRY_ENVIRONMENT - Environment name (default: production)
  BUGSINK_API_KEY    - API key for Bugsink
  BUGSINK_API_URL    - Bugsink server URL (e.g., https://errors.example.com)
  BUGSINK_TEAM       - Default team name
  BUGSINK_PROJECT    - Default project name
        """
    )

    parser.add_argument(
        "--dsn",
        help="Sentry/Bugsink DSN (skip API mode if provided)"
    )
    parser.add_argument(
        "--environment", "-e",
        default="production",
        help="Environment name (default: production)"
    )
    parser.add_argument(
        "--release", "-r",
        help="Release version"
    )
    parser.add_argument(
        "--update-dsn",
        action="store_true",
        help="Only update the DSN in existing configuration"
    )
    parser.add_argument(
        "--update-client",
        action="store_true",
        help="Update client code from templates"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Project root directory (default: current directory)"
    )

    # API Mode arguments
    parser.add_argument(
        "--api-key",
        help="Bugsink API key for automatic project setup"
    )
    parser.add_argument(
        "--api-url",
        help="Bugsink server URL (e.g., https://errors.example.com)"
    )
    parser.add_argument(
        "--team",
        help="Team name for API mode (creates if not exists)"
    )
    parser.add_argument(
        "--project",
        help="Project name for API mode (creates if not exists)"
    )

    args = parser.parse_args()

    if args.project_root:
        os.chdir(args.project_root)

    installer = ClientKitInstaller()
    sys.exit(installer.run(args))


if __name__ == "__main__":
    main()
