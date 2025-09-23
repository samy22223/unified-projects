"""
Setup script for Pinnacle AI Platform
"""
from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Pinnacle AI Platform - Comprehensive AI platform with 200+ agents, e-commerce functionality, and dropshipping automation"

# Read requirements from requirements.txt
def read_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="pinnacle-ai-platform",
    version="0.1.0",
    author="Pinnacle AI Team",
    author_email="team@pinnacle-ai.com",
    description="Comprehensive AI platform with 200+ agents, e-commerce functionality, and dropshipping automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/pinnacle-ai-platform",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: FastAPI",
        "Framework :: Django"
    ],
    python_requires=">=3.8",
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        "dev": read_requirements('requirements-dev.txt') if os.path.exists('requirements-dev.txt') else [],
        "docs": ["mkdocs>=1.5.3", "mkdocs-material>=9.4.8"],
        "ml": [
            "torch>=2.1.1", "torchvision>=0.16.1", "torchaudio>=2.1.1",
            "transformers>=4.35.2", "tokenizers>=0.15.0", "datasets>=2.15.0"
        ],
        "ecommerce": ["stripe>=7.8.1", "paypalrestsdk>=1.13.3"],
        "monitoring": ["sentry-sdk>=1.38.0", "prometheus-client>=0.19.0"]
    },
    entry_points={
        "console_scripts": [
            "pinnacle-ai=pinnacle_ai.cli:main",
            "pinnacle-manage=manage:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.yaml", "*.yml", "*.json", "*.cfg", "*.ini"],
    },
    data_files=[
        ("config", ["config/.env.example"]),
    ],
    zip_safe=False,
    project_urls={
        "Homepage": "https://github.com/your-username/pinnacle-ai-platform",
        "Documentation": "https://pinnacle-ai-platform.readthedocs.io/",
        "Repository": "https://github.com/your-username/pinnacle-ai-platform",
        "Issues": "https://github.com/your-username/pinnacle-ai-platform/issues",
        "Changelog": "https://github.com/your-username/pinnacle-ai-platform/blob/main/CHANGELOG.md",
    },
)