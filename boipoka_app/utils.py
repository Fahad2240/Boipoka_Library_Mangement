from .models import Subscription

def get_user_subscription(user):
    try:
        return Subscription.objects.get(user=user)
    except Subscription.DoesNotExist:
        return None  # or return a default subscription if appropriate
