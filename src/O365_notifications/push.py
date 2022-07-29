from O365_notifications.base import O365Notification, O365Subscriber


class O365PushNotification(O365Notification):
    pass


class O365PushSubscriber(O365Subscriber):
    def subscribe(self, *, resource):
        raise NotImplementedError("TODO: must implement this method.")

    @property
    def request_type(self):
        raise NotImplementedError("TODO: must implement this method.")
