from django import template
from django.utils import timezone
from datetime import datetime

register = template.Library()

@register.filter
def parse_datetime(value, format_str):
    # Check if the value is a datetime object
    if isinstance(value, datetime):
        # Ensure it is timezone-aware
        parsed_datetime = timezone.make_aware(value) if value.tzinfo is None else value
    else:
        try:
            # Parse the input date string to a datetime object
            parsed_datetime = timezone.make_aware(datetime.strptime(value, format_str))
        except ValueError:
            return None  # Return None if parsing fails

    now = timezone.now()  # Get the current timezone-aware datetime

    # Return True if the subscription is still valid, otherwise return False
    return now < parsed_datetime
