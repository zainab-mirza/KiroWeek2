"""Setup configuration for Email Summarizer."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = (
    readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""
)

setup(
    name="email-summarizer",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered email summarization with privacy focus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/email-summarizer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Email",
        "Topic :: Office/Business",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "Flask>=3.0.0",
        "Werkzeug>=3.0.0",
        "google-auth-oauthlib>=1.2.0",
        "google-api-python-client>=2.110.0",
        "msal>=1.26.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.0.0",
        "cryptography>=41.0.0",
        "keyring>=24.3.0",
        "transformers>=4.36.0",
        "torch>=2.1.0",
        "openai>=1.6.0",
        "pyyaml>=6.0.1",
        "requests>=2.31.0",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "hypothesis>=6.92.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "email-summarizer=email_summarizer.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "email_summarizer": [
            "web/templates/*.html",
        ],
    },
)
