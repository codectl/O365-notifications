from O365.mailbox import MailBox, Folder

from src.o365_notifications.streaming.base import O365StreamingNotifications


class O365MailBoxStreamingNotifications(O365StreamingNotifications):
    """ Streaming implementation for MailBox Streaming notifications """

    notifications_constructor = O365StreamingNotifications

    def __init__(self, *, parent, **kwargs):
        """ Mailbox Streaming Notifications

        :param parent: parent mailbox for this notification
        :type parent: Mailbox
        :param kwargs: any extra args to be passed to the StreamingNotifications instance
        :raises ValueError: if parent is not instance of Mailbox
        """
        if not isinstance(parent, MailBox):
            raise ValueError("'parent' must be instance of Mailbox")

        super().__init__(parent=parent, **kwargs)

    def resource_namespace(self, resource):
        """
        Get the full resource namespace for
        the folder resource.

        :param Folder resource: the resource
        :return: the full resource namespace
        """
        if not isinstance(resource, Folder):
            raise ValueError("'resource' must be instance of Folder")

        return resource.build_url(resource._endpoints.get('folder_messages').format(
            id=resource.folder_id) if resource else resource._endpoints.get('root_messages'))
