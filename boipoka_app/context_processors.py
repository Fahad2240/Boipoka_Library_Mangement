# boipoka_app/context_processors.py

from .models import Notifications

def unread_notifications(request):
    if request.user.is_authenticated:
        temp=Notifications.objects.filter(subscriber=request.user, is_read=False)#Fetch all notifications which are unread
        if temp.exists():
            unread_count = temp.count()
        else:
            unread_count = None
    else:
        unread_count = None

    return {
        'unread_notifications_count': unread_count,
    }
