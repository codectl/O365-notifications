from O365.mailbox import MailBox, Folder

from O365_notifications.streaming.base import O365StreamingNotifications


class O365MailBoxStreamingNotifications(O365StreamingNotifications):
    notifications_constructor = O365StreamingNotifications

    def __init__(self, *, parent: MailBox, **kwargs):
        if not isinstance(parent, MailBox):
            raise ValueError("'parent' must be instance of Mailbox")

        super().__init__(parent=parent, **kwargs)

    def resource_namespace(self, resource: Folder) -> str:
        """Get the full resource namespace for the folder resource."""
        if not isinstance(resource, Folder):
            raise ValueError("'resource' must be instance of Folder")

        endpoints = resource._endpoints
        return resource.build_url(
            endpoints.get("folder_messages").format(id=resource.folder_id)
            if resource
            else endpoints.get("root_messages")
        )
