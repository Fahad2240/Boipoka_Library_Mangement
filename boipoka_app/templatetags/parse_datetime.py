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
            return "Invalid date format."

    now = timezone.now()  # Get the current timezone-aware datetime

    # Compare the parsed datetime with the current datetime
    if now < parsed_datetime:
        return "You still have a subscription."
    else:
        return "You are expired."
