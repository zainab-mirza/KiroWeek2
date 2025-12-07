# Contributing to Email Summarizer

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/yourusername/email-summarizer.git
cd email-summarizer
```

3. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

4. Install dependencies including dev tools:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov hypothesis
```

## Project Structure

```
email_summarizer/
├── auth/              # OAuth authentication
├── config/            # Configuration management
├── fetcher/           # Email fetching
├── preprocessor/      # Email cleaning
├── summarizer/        # AI summarization
├── storage/           # Data persistence
├── orchestrator/      # Pipeline coordination
├── web/               # Flask server & UI
├── utils/             # Utilities
├── models.py          # Data models
├── crypto.py          # Encryption
└── cli.py             # CLI interface
```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=email_summarizer

# Run specific test file
pytest tests/test_models.py
```

### Writing Tests

- Write unit tests for new functionality
- Use property-based tests (Hypothesis) for universal properties
- Mock external services (email APIs, LLM APIs)
- Test edge cases and error conditions

Example:
```python
def test_email_cleaning():
    """Test that HTML is properly cleaned."""
    preprocessor = EmailPreprocessor()
    raw_email = create_test_email(body_html="<p>Hello</p>")
    cleaned = preprocessor.clean_email(raw_email)
    assert "<p>" not in cleaned.cleaned_body
    assert "Hello" in cleaned.cleaned_body
```

## Making Changes

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Commit with clear messages:
```bash
git commit -m "Add feature: description of what you added"
```

6. Push to your fork:
```bash
git push origin feature/your-feature-name
```

7. Open a Pull Request

## Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Ensure all tests pass
- Update documentation if needed
- Keep PRs focused on a single feature or fix

## Areas for Contribution

### High Priority
- Additional email provider support (Yahoo, ProtonMail, etc.)
- More local model options
- Improved action item extraction
- Better deadline detection
- Mobile-responsive UI improvements

### Medium Priority
- Scheduled processing (cron integration)
- Email filtering rules
- Custom summarization prompts
- Export functionality (CSV, PDF)
- Search improvements

### Low Priority
- Multi-account support
- Analytics and insights
- Browser extension
- Desktop notifications

## Bug Reports

When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output from `~/.email-summarizer/logs/app.log`

## Feature Requests

When requesting features:
- Describe the use case
- Explain why it would be valuable
- Suggest implementation approach if possible
- Consider privacy implications

## Code Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged
4. Your contribution will be credited in the release notes

## Questions?

- Open an issue for questions
- Check existing issues and PRs first
- Be respectful and constructive

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
