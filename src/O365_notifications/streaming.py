import json
import logging
import requests
import typing

from O365.utils import ApiComponent

from O365_notifications import utils
from O365_notifications.base import (
    O365_BASE,
    O365Notification,
    O365Subscriber,
    O365NotificationsHandler,
)

__all__ = ("O365StreamingNotification", "O365StreamingSubscriber")

logger = logging.getLogger(__name__)


class O365StreamingNotification(O365Notification):
    pass


class O365StreamingSubscriber(O365Subscriber):
    _endpoints = {
        "subscriptions": "/subscriptions",
        "notifications": "/GetNotifications",
    }
    _namespace = f"{O365_BASE}.StreamingSubscription"
    streaming_notification_constructor = O365StreamingNotification

    # Streaming connection settings
    _default_connection_timeout_in_minutes = 120  # Equivalent to 2 hours
    _default_keep_alive_notification_interval_in_seconds = 5

    def __init__(self, *, parent=None, con=None, **kwargs):
        super().__init__(parent=parent, con=con, **kwargs)

    @property
    def namespace(self):
        return self._namespace

    def subscribe(self, *, resource: ApiComponent, event: O365Notification.Event) -> \
            typing.Optional[str]:
        url = self.build_url(self._endpoints.get("subscriptions"))

        if resource not in self.resources:
            self.resources.append(resource)

        data = {
            "@odata.type": self.namespace,
            self._cc("resource"): utils.resolve_namespace(resource),
            self._cc("changeType"): self.event,
        }

        try:
            response = self.con.post(url, data)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == requests.codes.too_many_requests:
                logger.warning("Too many requests...")
                logger.info(str(e.response.headers))
                logger.warning("Raising exception...")
                raise e
        else:
            if not response:
                return None

            notification = response.json()
            self.subscriptions.append(notification["Id"])

            msg = f"Subscribed to resource '{resource}': Response: '{notification}'"
            logger.debug(msg)

    def create_event_channel(
        self,
        *,
        notification_handler: O365NotificationsHandler = None,
        connection_timeout: int = _default_connection_timeout_in_minutes,
        keep_alive_interval: int = _default_keep_alive_notification_interval_in_seconds,
        refresh_after_expire: bool = False,
    ):
        """
        Create a new channel for events.

        :param notification_handler: the notification's handler
        :param connection_timeout: time in minutes in which connection closes
        :param keep_alive_interval: time interval in seconds in which a message is sent
        :param refresh_after_expire: refresh when http connection expires
        :raises ValueError: if no subscription is provided
        :raises Exception: if streaming error occurs
        """
        if not self.subscriptions:
            raise ValueError("Can't start streaming connection without subscription.")

        notification_handler = notification_handler or O365NotificationsHandler()
        url = self.build_url(self._endpoints.get("notifications"))

        data = {
            self._cc("connectionTimeoutInMinutes"): connection_timeout,
            self._cc("keepAliveNotificationIntervalInSeconds"): keep_alive_interval,
            self._cc("subscriptionIds"): self.subscriptions,
        }

        logger.info("Open new events channel ...")
        while True:
            try:
                response = self.con.post(url, data, stream=True)
                logger.debug("Start streaming cycle ...")

            # Renew subscriptions if 404 is raised
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == requests.codes.not_found:
                    logger.debug("Expired subscription. Renewing subscriptions...")
                    data[self._cc("subscriptionIds")] = self.renew_subscriptions()

                    msg = f"Renewed subscriptions: {data[self._cc('subscriptionIds')]}"
                    logger.debug(msg)
                    continue
                # raise for any other error
                raise e
            else:
                if not response:
                    return

            # Use 'with' clause to prevent requests.exceptions.ChunkedEncodingError.
            # Exception occurs when connection is closed by the server causing
            # partially reading the request body.
            with response:
                stream_data = b""
                bracket_control = []
                for starting_chunk in response.iter_content(chunk_size=1):
                    # Reading json group values...
                    if starting_chunk == b"[":
                        bracket_control.append(starting_chunk)
                        try:
                            for chunk in response.iter_content(chunk_size=1):
                                # Grouping json objects
                                if chunk == b"{":
                                    bracket_control.append(chunk)
                                elif chunk == b"}":
                                    bracket_control.remove(b"{")
                                elif chunk == b"]":
                                    bracket_control.remove(b"[")

                                # Control to see if json object is complete
                                if b"{" in bracket_control:
                                    stream_data += chunk
                                elif b"[" in bracket_control:
                                    if stream_data:
                                        stream_data += b"}"
                                        notification = (
                                            self.streaming_notification_constructor(
                                                parent=self,
                                                **json.loads(
                                                    stream_data.decode("utf-8")
                                                ),
                                            )
                                        )
                                        notification_handler.process(notification)
                                        stream_data = b""
                                else:
                                    # Break outer loop
                                    bracket_control.append(True)
                                    break  # Connection timed out

                        except Exception as e:
                            if isinstance(e, requests.exceptions.ChunkedEncodingError):
                                # Seem like empty values in the connection, is causing
                                # the communication to be corrupted. When that happens,
                                # the loop is interrupted and the streaming is restarted
                                logger.warning(f"Exception suppressed: {e}")
                                break
                            # raise for any other error
                            raise e
                    if bracket_control:
                        # Break loop since all data is read
                        break

            # Automatically refresh HTTP connection after it expires
            if refresh_after_expire:
                logger.debug("Refreshing connection ...")
            else:
                break

        logger.info("Stopped listening for events: connection closed.")
