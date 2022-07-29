from O365.mailbox import MailBox, Folder

from O365_notifications.streaming.base import O365StreamingNotifications

__all__ = ("O365MailBoxStreamingNotifications",)


class O365MailBoxStreamingNotifications(O365StreamingNotifications):
    notifications_constructor = O365StreamingNotifications

    def __init__(self, *, parent: MailBox, **kwargs):
        if not isinstance(parent, MailBox):
            raise ValueError("'parent' must be instance of Mailbox")

        super().__init__(parent=parent, **kwargs)

    def resource_namespace(self, folder: Folder) -> str:
        """Get the full resource namespace for the folder resource."""
        if not isinstance(folder, Folder):
            raise ValueError("'resource' must be instance of Folder")

        endpoints = folder._endpoints
        return folder.build_url(
            endpoints.get("folder_messages").format(id=folder.folder_id)
            if folder
            else endpoints.get("root_messages")
        )
