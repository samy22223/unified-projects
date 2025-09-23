#!/usr/bin/env python3
"""
Pinnacle AI Platform - Command Line Interface

This script provides command-line utilities for managing the Pinnacle AI Platform.

Usage:
    python scripts/cli.py [command] [options]
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional


class PinnacleCLI:
    """Command-line interface for Pinnacle AI Platform."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"

    def run_command(self, command: List[str], cwd: Path = None) -> bool:
        """Run a command and return success status."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
            return False

    def activate_venv(self):
        """Activate virtual environment if it exists."""
        if self.venv_path.exists():
            if sys.platform == "win32":
                activate_script = self.venv_path / "Scripts" / "activate.bat"
                os.system(f'"{activate_script}"')
            else:
                activate_script = self.venv_path / "bin" / "activate"
                os.system(f"source {activate_script}")

    def start_server(self, host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
        """Start the development server."""
        print(f"🚀 Starting development server on {host}:{port}")

        cmd = [
            sys.executable, "-m", "uvicorn",
            "app:app",
            "--host", host,
            "--port", str(port)
        ]

        if reload:
            cmd.append("--reload")

        try:
            subprocess.run(cmd, cwd=self.project_root)
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

    def run_tests(self, test_type: str = "all", coverage: bool = False):
        """Run tests with optional coverage."""
        print("🧪 Running tests...")

        cmd = [sys.executable, "-m", "pytest"]

        if test_type == "unit":
            cmd.append("tests/unit/")
        elif test_type == "integration":
            cmd.append("tests/integration/")
        elif test_type == "e2e":
            cmd.append("tests/e2e/")
        else:
            cmd.extend(["tests/unit/", "tests/integration/"])

        if coverage:
            cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])

        return self.run_command(cmd)

    def format_code(self):
        """Format code using black and isort."""
        print("🎨 Formatting code...")

        # Format with black
        if not self.run_command([sys.executable, "-m", "black", "."]):
            return False

        # Sort imports with isort
        if not self.run_command([sys.executable, "-m", "isort", "."]):
            return False

        print("✅ Code formatted successfully")
        return True

    def lint_code(self):
        """Lint code using flake8 and mypy."""
        print("🔍 Linting code...")

        # Run flake8
        if not self.run_command([sys.executable, "-m", "flake8", "src/"]):
            return False

        # Run mypy
        if not self.run_command([sys.executable, "-m", "mypy", "src/"]):
            return False

        print("✅ Code linting passed")
        return True

    def setup_docker(self):
        """Set up Docker development environment."""
        print("🐳 Setting up Docker environment...")

        if not self.run_command(["docker-compose", "up", "-d"]):
            print("❌ Failed to start Docker environment")
            return False

        print("✅ Docker environment started")
        print("🌐 Application: http://localhost:8000")
        print("📊 Database: localhost:5432")
        print("⚡ Redis: localhost:6379")
        return True

    def create_migration(self, name: str):
        """Create a new database migration."""
        print(f"📄 Creating migration: {name}")

        cmd = [sys.executable, "manage.py", "makemigrations", name]
        return self.run_command(cmd)

    def run_migration(self):
        """Run database migrations."""
        print("🔄 Running migrations...")

        cmd = [sys.executable, "manage.py", "migrate"]
        return self.run_command(cmd)

    def create_superuser(self):
        """Create a Django superuser."""
        print("👤 Creating superuser...")

        cmd = [sys.executable, "manage.py", "createsuperuser", "--noinput"]
        return self.run_command(cmd)

    def collect_static(self):
        """Collect static files."""
        print("📁 Collecting static files...")

        cmd = [sys.executable, "manage.py", "collectstatic", "--noinput"]
        return self.run_command(cmd)

    def shell(self):
        """Open Django shell."""
        print("🐚 Opening Django shell...")

        cmd = [sys.executable, "manage.py", "shell"]
        subprocess.run(cmd, cwd=self.project_root)

    def setup_project(self):
        """Run the project setup script."""
        print("⚙️  Running project setup...")

        cmd = [sys.executable, "scripts/setup_project.py"]
        return self.run_command(cmd)

    def backup_database(self):
        """Create a database backup."""
        print("💾 Creating database backup...")

        backup_dir = self.project_root / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = subprocess.check_output(["date", "+%Y%m%d_%H%M%S"]).decode().strip()
        backup_file = backup_dir / f"pinnacle_ai_backup_{timestamp}.sql"

        cmd = [
            "pg_dump",
            "-h", "localhost",
            "-U", "pinnacle_user",
            "-d", "pinnacle_ai",
            "-f", str(backup_file)
        ]

        print(f"Creating backup: {backup_file}")
        return self.run_command(cmd)

    def restore_database(self, backup_file: str):
        """Restore database from backup."""
        print(f"🔄 Restoring database from: {backup_file}")

        cmd = [
            "psql",
            "-h", "localhost",
            "-U", "pinnacle_user",
            "-d", "pinnacle_ai",
            "-f", backup_file
        ]

        return self.run_command(cmd)

    def show_status(self):
        """Show project status and health."""
        print("📊 Project Status")
        print("=" * 40)

        # Check virtual environment
        venv_exists = self.venv_path.exists()
        print(f"Virtual Environment: {'✅' if venv_exists else '❌'}")

        # Check .env file
        env_exists = (self.project_root / ".env").exists()
        print(f"Environment Config: {'✅' if env_exists else '❌'}")

        # Check Docker
        docker_available = self.run_command(["docker", "--version"])
        print(f"Docker Available: {'✅' if docker_available else '❌'}")

        # Check database
        db_available = self.run_command(["pg_isready", "-h", "localhost"])
        print(f"Database Available: {'✅' if db_available else '❌'}")

        # Check Redis
        redis_available = self.run_command(["redis-cli", "ping"])
        print(f"Redis Available: {'✅' if redis_available else '❌'}")

        print("\n📋 Quick Actions:")
        print("  Start server: python scripts/cli.py server")
        print("  Run tests: python scripts/cli.py test")
        print("  Format code: python scripts/cli.py format")
        print("  Setup Docker: python scripts/cli.py docker")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Pinnacle AI Platform CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cli.py server                    # Start development server
  python scripts/cli.py test --coverage          # Run tests with coverage
  python scripts/cli.py format                   # Format code
  python scripts/cli.py lint                     # Lint code
  python scripts/cli.py docker                   # Setup Docker environment
  python scripts/cli.py status                   # Show project status
  python scripts/cli.py setup                    # Run project setup
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Server command
    subparsers.add_parser("server", help="Start development server")

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--type", choices=["unit", "integration", "e2e", "all"],
                           default="all", help="Test type to run")
    test_parser.add_argument("--coverage", action="store_true", help="Generate coverage report")

    # Format command
    subparsers.add_parser("format", help="Format code with black and isort")

    # Lint command
    subparsers.add_parser("lint", help="Lint code with flake8 and mypy")

    # Docker command
    subparsers.add_parser("docker", help="Setup Docker development environment")

    # Database commands
    subparsers.add_parser("migrate", help="Run database migrations")
    subparsers.add_parser("makemigrations", help="Create new migrations")

    # Setup command
    subparsers.add_parser("setup", help="Run project setup")

    # Status command
    subparsers.add_parser("status", help="Show project status")

    # Backup command
    subparsers.add_parser("backup", help="Create database backup")

    # Shell command
    subparsers.add_parser("shell", help="Open Django shell")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = PinnacleCLI()

    # Handle commands
    if args.command == "server":
        cli.start_server()
    elif args.command == "test":
        cli.run_tests(args.type, args.coverage)
    elif args.command == "format":
        cli.format_code()
    elif args.command == "lint":
        cli.lint_code()
    elif args.command == "docker":
        cli.setup_docker()
    elif args.command == "migrate":
        cli.run_migration()
    elif args.command == "makemigrations":
        name = input("Migration name: ")
        cli.create_migration(name)
    elif args.command == "setup":
        cli.setup_project()
    elif args.command == "status":
        cli.show_status()
    elif args.command == "backup":
        cli.backup_database()
    elif args.command == "shell":
        cli.shell()


if __name__ == "__main__":
    main()