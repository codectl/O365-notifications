from O365_notifications.base import O365Notification, O365Notifications


class O365PushNotification(O365Notification):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)


class O365PushNotifications(O365Notifications):
    def subscribe(self, *, resource):
        raise NotImplementedError("TODO: must implement this method.")

    @property
    def request_type(self):
        raise NotImplementedError("TODO: must implement this method.")
