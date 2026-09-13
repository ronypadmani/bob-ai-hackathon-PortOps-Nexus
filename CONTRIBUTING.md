# Contributing to Port Operations Copilot

Thank you for your interest in contributing to the **Port Operations Copilot** project for the IBM Bob Hackathon.

## Hackathon Submission Guidelines

1. **Repository Structure**: Keep all core application code in `src/`, written documentation in `docs/`, demo links and screenshots in `demo/`, and presentation slides in `presentation/`.
2. **Environment Variables**: Never commit real credentials or `.env` files. Ensure all configuration parameters are documented in `src/.env.example`.
3. **Automated Validation**: Ensure the GitHub Action `.github/workflows/validate.yml` passes before submission.
4. **Code Quality**: All modules must include docstrings, strict type annotations, and passing automated tests in `src/tests/`.

## Running the Verification Suite
```bash
pytest src/tests/ -v
```
