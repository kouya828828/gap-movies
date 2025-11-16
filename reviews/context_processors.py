# reviews/context_processors.py

def unread_notifications(request):
    """すべてのテンプレートで未読通知件数を使えるようにする"""
    if request.user.is_authenticated:
        from .models import Notification
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}