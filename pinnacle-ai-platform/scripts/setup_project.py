#!/usr/bin/env python3
"""
Pinnacle AI Platform - Project Setup Script

This script handles the initial setup and configuration of the Pinnacle AI Platform.
It creates necessary directories, sets up configuration files, and prepares the
development environment.

Usage:
    python scripts/setup_project.py [--env development|production] [--clean]
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


class ProjectSetup:
    """Handles project setup and configuration."""

    def __init__(self, project_root: str = None):
        """Initialize setup with project root directory."""
        self.project_root = Path(project_root or os.getcwd())
        self.src_dir = self.project_root / "src"
        self.config_dir = self.project_root / "config"
        self.scripts_dir = self.project_root / "scripts"
        self.docs_dir = self.project_root / "docs"

    def run_command(self, command: str, cwd: Path = None) -> bool:
        """Run a shell command and return success status."""
        try:
            result = subprocess.run(
                command.split(),
                cwd=cwd or self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✓ {command}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ {command} failed: {e.stderr}")
            return False

    def create_directory_structure(self):
        """Create the complete project directory structure."""
        print("📁 Creating directory structure...")

        directories = [
            self.src_dir / "core" / "ai",
            self.src_dir / "core" / "auth",
            self.src_dir / "core" / "database",
            self.src_dir / "core" / "config",
            self.src_dir / "services" / "ecommerce",
            self.src_dir / "services" / "dropshipping",
            self.src_dir / "services" / "integrations",
            self.src_dir / "services" / "agents",
            self.src_dir / "api" / "v1",
            self.src_dir / "api" / "common",
            self.src_dir / "utils",
            self.src_dir / "tests",
            self.docs_dir / "api",
            self.docs_dir / "deployment",
            self.docs_dir / "development",
            self.docs_dir / "guides",
            self.project_root / "tests" / "unit",
            self.project_root / "tests" / "integration",
            self.project_root / "tests" / "e2e",
            self.project_root / "monitoring",
            self.project_root / "deployment" / "docker",
            self.project_root / "deployment" / "kubernetes",
            self.project_root / "assets" / "images",
            self.project_root / "assets" / "icons",
            self.project_root / "assets" / "docs",
            self.config_dir,
            self.scripts_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {directory.relative_to(self.project_root)}")

    def create_initial_files(self):
        """Create initial Python package files."""
        print("📄 Creating initial package files...")

        # Create __init__.py files
        init_dirs = [
            self.src_dir,
            self.src_dir / "core",
            self.src_dir / "core" / "ai",
            self.src_dir / "core" / "auth",
            self.src_dir / "core" / "database",
            self.src_dir / "core" / "config",
            self.src_dir / "services",
            self.src_dir / "services" / "ecommerce",
            self.src_dir / "services" / "dropshipping",
            self.src_dir / "services" / "integrations",
            self.src_dir / "services" / "agents",
            self.src_dir / "api",
            self.src_dir / "api" / "v1",
            self.src_dir / "api" / "common",
            self.src_dir / "utils",
            self.src_dir / "tests",
        ]

        for directory in init_dirs:
            init_file = directory / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Initial package file."""\n')
                print(f"  Created: {init_file.relative_to(self.project_root)}")

    def setup_virtual_environment(self):
        """Create and configure virtual environment."""
        print("🐍 Setting up virtual environment...")

        venv_path = self.project_root / "venv"

        if not venv_path.exists():
            if not self.run_command("python -m venv venv"):
                print("⚠️  Failed to create virtual environment")
                return False

        # Upgrade pip
        if sys.platform == "win32":
            pip_cmd = "venv\\Scripts\\pip"
        else:
            pip_cmd = "venv/bin/pip"

        if not self.run_command(f"{pip_cmd} install --upgrade pip"):
            return False

        return True

    def install_dependencies(self):
        """Install project dependencies."""
        print("📦 Installing dependencies...")

        if not self.setup_virtual_environment():
            return False

        # Install requirements
        if sys.platform == "win32":
            pip_cmd = "venv\\Scripts\\pip"
        else:
            pip_cmd = "venv/bin/pip"

        if not self.run_command(f"{pip_cmd} install -r requirements.txt"):
            return False

        return True

    def setup_pre_commit_hooks(self):
        """Set up pre-commit hooks for code quality."""
        print("🔧 Setting up pre-commit hooks...")

        if not self.run_command("pip install pre-commit"):
            return False

        # Initialize pre-commit
        if not self.run_command("pre-commit install"):
            return False

        return True

    def create_env_file(self, env_type: str = "development"):
        """Create environment configuration file."""
        print(f"⚙️  Creating {env_type} environment configuration...")

        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"

        if env_example.exists():
            shutil.copy(env_example, env_file)
            print(f"  Created: {env_file.relative_to(self.project_root)}")
        else:
            print("⚠️  .env.example not found, skipping .env creation")

    def setup_docker(self):
        """Create Docker configuration files."""
        print("🐳 Setting up Docker configuration...")

        dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    redis-tools \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Start application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
'''

        docker_compose_content = '''version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/pinnacle_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
      - /app/__pycache__
    command: uvicorn app:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=pinnacle_ai
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
'''

        # Create Dockerfile
        dockerfile_path = self.project_root / "Dockerfile"
        if not dockerfile_path.exists():
            dockerfile_path.write_text(dockerfile_content)
            print(f"  Created: {dockerfile_path.relative_to(self.project_root)}")

        # Create docker-compose.yml
        compose_path = self.project_root / "docker-compose.yml"
        if not compose_path.exists():
            compose_path.write_text(docker_compose_content)
            print(f"  Created: {compose_path.relative_to(self.project_root)}")

    def create_gitignore(self):
        """Create .gitignore file if it doesn't exist."""
        gitignore_path = self.project_root / ".gitignore"

        if not gitignore_path.exists():
            gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
*.log
logs/
data/
cache/
temp/
uploads/

# Secrets
secrets/
*.key
*.pem
*.crt

# Model files
models/
*.h5
*.pb
*.onnx
*.pkl
"""
            gitignore_path.write_text(gitignore_content)
            print(f"  Created: {gitignore_path.relative_to(self.project_root)}")

    def run(self, env_type: str = "development", clean: bool = False):
        """Run the complete setup process."""
        print("🚀 Starting Pinnacle AI Platform setup...")
        print(f"Project root: {self.project_root}")
        print(f"Environment: {env_type}")
        print("-" * 50)

        if clean:
            print("🧹 Clean setup requested...")

        # Create directory structure
        self.create_directory_structure()

        # Create initial files
        self.create_initial_files()

        # Create configuration files
        self.create_gitignore()
        self.create_env_file(env_type)

        # Setup Docker
        self.setup_docker()

        # Install dependencies
        if not clean:
            self.install_dependencies()

        # Setup pre-commit hooks
        if not clean:
            self.setup_pre_commit_hooks()

        print("-" * 50)
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Review and update .env file with your configuration")
        print("2. Run 'python scripts/setup_project.py' to verify setup")
        print("3. Start development: 'docker-compose up' or 'uvicorn app:app --reload'")
        print("4. Visit http://localhost:8000/docs for API documentation")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Setup Pinnacle AI Platform")
    parser.add_argument(
        "--env",
        choices=["development", "production"],
        default="development",
        help="Environment type (default: development)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean setup without installing dependencies"
    )
    parser.add_argument(
        "--project-root",
        help="Project root directory"
    )

    args = parser.parse_args()

    try:
        setup = ProjectSetup(args.project_root)
        setup.run(args.env, args.clean)
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()