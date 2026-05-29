"""Briefing command — generate and return a digest."""

from cli import api_client


def cmd_briefing(time_of_day: str = "morning") -> dict:
    """Run the full pipeline and return the result.

    Parameters
    ----------
    time_of_day : str
        "morning" or "evening" — currently passed as context to the pipeline.
    """
    result = api_client.run_pipeline("full")
    result["requested_time"] = time_of_day
    return result
