from O365_notifications.base import O365Notification, O365Notifications


class O365PushNotification(O365Notification):
    pass


class O365PushNotifications(O365Notifications):
    def subscribe(self, *, resource):
        raise NotImplementedError("TODO: must implement this method.")

    @property
    def request_type(self):
        raise NotImplementedError("TODO: must implement this method.")
