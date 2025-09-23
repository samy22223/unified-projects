# Contributing to Pinnacle AI Platform

Thank you for your interest in contributing to the Pinnacle AI Platform! We welcome contributions from everyone. This document will help you get started with contributing to our project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Workflow](#contributing-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Feature Requests](#feature-requests)
- [Community](#community)

## 🎯 Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.8 or higher
- **Git**: 2.25 or higher
- **Docker**: 20.0 or higher (optional)
- **PostgreSQL**: 12.0 or higher (optional)
- **Redis**: 6.0 or higher (optional)

### Fork the Repository

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/pinnacle-ai-platform.git
   cd pinnacle-ai-platform
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/pinnacle-ai/pinnacle-ai-platform.git
   ```

### Development Setup

1. **Set up virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run setup script**:
   ```bash
   python scripts/setup_project.py
   ```

5. **Start development server**:
   ```bash
   uvicorn app:app --reload
   ```

## 🛠️ Development Setup

### Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
# Required
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/pinnacle_ai
REDIS_URL=redis://localhost:6379/0

# AI Services (optional for development)
OPENAI_API_KEY=your-openai-key
HUGGINGFACE_API_TOKEN=your-hf-token

# Development
DEBUG=True
LOG_LEVEL=DEBUG
```

### Database Setup

```bash
# Create database
createdb pinnacle_ai

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Docker Development

```bash
# Start all services
docker-compose up -d

# Run tests
docker-compose exec app pytest

# View logs
docker-compose logs -f
```

## 🔄 Contributing Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number
# or
git checkout -b docs/update-documentation
```

### 2. Make Changes

- Follow the [code style](#code-style) guidelines
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Run with coverage
pytest --cov=src --cov-report=html
```

### 4. Format and Lint

```bash
# Format code
black .
isort .

# Lint code
flake8 src/
mypy src/

# Run all checks
pre-commit run --all-files
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat: add new AI agent for customer support

- Add CustomerSupportAgent class
- Implement chat functionality
- Add unit tests
- Update documentation

Closes #123"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## 📝 Code Style

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some additional conventions:

- **Line length**: 88 characters (Black default)
- **Import order**: Use `isort` configuration
- **Type hints**: Required for all new functions and methods
- **Docstrings**: Google style docstrings for public APIs

### Code Formatting

```bash
# Format with Black
black src/ tests/ scripts/

# Sort imports with isort
isort src/ tests/ scripts/

# Both
black src/ tests/ scripts/ && isort src/ tests/ scripts/
```

### Naming Conventions

- **Classes**: `CamelCase` (e.g., `CustomerSupportAgent`)
- **Functions**: `snake_case` (e.g., `process_customer_query`)
- **Variables**: `snake_case` (e.g., `customer_data`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Modules**: `snake_case` (e.g., `customer_support.py`)

### Type Hints

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class CustomerQuery(BaseModel):
    query: str
    customer_id: int
    priority: str = "normal"

def process_query(query: CustomerQuery) -> Dict[str, Any]:
    """Process a customer query and return response."""
    pass
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
└── fixtures/      # Test fixtures and data
```

### Writing Tests

```python
import pytest
from src.services.agents.customer_support import CustomerSupportAgent

class TestCustomerSupportAgent:
    def test_process_query(self):
        agent = CustomerSupportAgent()
        result = agent.process_query("How do I reset my password?")
        assert result["status"] == "success"

    def test_invalid_query(self):
        agent = CustomerSupportAgent()
        with pytest.raises(ValueError):
            agent.process_query("")
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_customer_support.py

# Specific test class
pytest tests/unit/test_customer_support.py::TestCustomerSupportAgent

# Run tests matching pattern
pytest -k "customer_support"
```

## 📚 Documentation

### Documentation Structure

```
docs/
├── api/           # API documentation
├── deployment/    # Deployment guides
├── development/   # Development guides
├── guides/        # User guides
├── architecture/  # Architecture docs
└── contributing/  # Contributing guidelines
```

### Writing Documentation

- Use [Markdown](https://www.markdownguide.org/) for documentation
- Include code examples and screenshots when relevant
- Keep documentation up-to-date with code changes
- Use clear, concise language

### API Documentation

Document all public APIs using docstrings:

```python
def create_customer_agent(customer_id: int) -> CustomerSupportAgent:
    """Create a customer support agent for the given customer.

    Args:
        customer_id: The unique identifier for the customer

    Returns:
        CustomerSupportAgent: Configured agent for the customer

    Raises:
        ValueError: If customer_id is invalid

    Example:
        >>> agent = create_customer_agent(12345)
        >>> response = agent.process_query("Help!")
    """
    pass
```

## 🔀 Pull Request Process

### Before Submitting

- [ ] Ensure all tests pass
- [ ] Format code with Black and isort
- [ ] Run linting checks
- [ ] Update documentation
- [ ] Add changelog entry

### Pull Request Template

```markdown
## Description

Brief description of the changes

## Related Issues

Closes #123, #456

## Changes Made

- Added new feature X
- Fixed bug Y
- Updated documentation Z

## Testing

- Added unit tests for new functionality
- Updated integration tests
- Manual testing completed

## Screenshots

[If applicable, add screenshots]

## Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] All tests pass
```

### Review Process

1. **Automated checks**: CI/CD pipeline runs tests and linting
2. **Code review**: At least one maintainer reviews the code
3. **Testing**: Changes are tested in staging environment
4. **Merge**: Approved PRs are merged by maintainers

## 🐛 Issue Reporting

### Bug Reports

When reporting bugs, please include:

- **Description**: Clear description of the bug
- **Steps to reproduce**: Step-by-step instructions
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: Python version, OS, dependencies
- **Screenshots**: If applicable

### Feature Requests

When requesting features, please include:

- **Description**: Clear description of the feature
- **Use case**: Why is this feature needed?
- **Proposed solution**: How should it work?
- **Alternatives**: Other solutions considered
- **Additional context**: Screenshots, examples, etc.

## 🎯 Feature Requests

### Request Template

```markdown
## Feature Description

Describe the feature you want to add

## Use Case

Explain why this feature is needed and how it would be used

## Proposed Solution

Describe how you think this feature should work

## Alternatives Considered

List any alternative solutions you've considered

## Additional Context

Add any other context, screenshots, or examples
```

## 🌟 Community

### Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and discussions
- **Discord**: Join our community Discord server
- **Email**: For private inquiries: contact@pinnacle-ai.com

### Contributing to Different Areas

- **🐍 Core Development**: Python, AI/ML, APIs
- **🎨 Frontend**: Web interfaces, dashboards
- **📚 Documentation**: Guides, API docs, tutorials
- **🧪 Testing**: Test automation, quality assurance
- **🚀 DevOps**: CI/CD, deployment, monitoring
- **🎯 Product**: Feature design, user experience

### Recognition

Contributors are recognized through:

- **GitHub**: All contributors listed in README
- **Changelog**: Major contributions mentioned
- **Newsletter**: Community highlights
- **Swag**: T-shirts, stickers for active contributors

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same license as the original project (MIT License).

## 🙏 Acknowledgments

Thank you to all our contributors! Your efforts help make the Pinnacle AI Platform better for everyone.

---

*Happy contributing! 🎉*