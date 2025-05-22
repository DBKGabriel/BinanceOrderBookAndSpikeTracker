import pytz
from datetime import datetime

# Define timezones
utc = pytz.utc
eastern = pytz.timezone("US/Eastern")

def utc_to_eastern(timestamp_utc):
    """Convert UTC timestamp to Eastern time."""
    if isinstance(timestamp_utc, int) or isinstance(timestamp_utc, float):
        timestamp_utc = datetime.utcfromtimestamp(timestamp_utc / 1000).replace(tzinfo=utc)
    elif not timestamp_utc.tzinfo:
        timestamp_utc = timestamp_utc.replace(tzinfo=utc)
    
    return timestamp_utc.astimezone(eastern)

def format_timestamp(timestamp, format_str="%Y-%m-%d %H:%M:%S"):
    """Format a timestamp as a string."""
    if isinstance(timestamp, datetime):
        return timestamp.strftime(format_str)
    return timestamp
