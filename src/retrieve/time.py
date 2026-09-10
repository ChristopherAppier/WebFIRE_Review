import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def check_timer(config):
    """Returns the start and end date to be used for the WebFIRE API request

    Args:
        config (dict): A dictionary containing configuration settings.

    Returns:
        dict: A dictionary containing the start and end dates in MM/DD/YYYY format.
    """

    logging.info(f"\n{'*' * 50}\n\nLoading timestamps from settings.yml")

    # Read last_run_timestamp
    last_run = config["last_run_timestamp"]

    # Calculate default if first run, otherwise uses settings.yml last run timestamp
    default_interval = config.get("default_interval_days")
    if not last_run:
        start = datetime.utcnow() - timedelta(days=default_interval)
    else:
        start = last_run

    start = convert_date(start)

    # Current time is end
    end = datetime.utcnow()
    end = convert_date(end)

    return {
        "start_date": start,
        "end_date": end,
    }


def convert_date(iso_date):
    """Convert date string (any common format) to MM/DD/YYYY

    Args:
        iso_date (str): The date string to be converted.

    Returns:
        str: The date in MM/DD/YYYY format.
    """
    date_part = str(iso_date)[:10]  # Grab YYYY-MM-DD from whatever format arrives
    dt = datetime.strptime(date_part, "%Y-%m-%d")
    return dt.strftime("%m/%d/%Y")
