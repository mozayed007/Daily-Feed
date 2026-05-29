"""Trends command — detect emerging trends via the pipeline."""

from cli import api_client


def cmd_trends() -> dict:
    """Run the trends pipeline and return the result."""
    return api_client.run_pipeline("trends")
