"""Счётчик непрочитанных уведомлений на всех страницах (FR-24)."""


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {"unread_notifications": 0}
    return {
        "unread_notifications": request.user.notifications.filter(is_read=False).count()
    }
