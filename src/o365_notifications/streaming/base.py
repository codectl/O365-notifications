import json
import logging
import requests
from abc import abstractmethod

from src.o365_notifications.base import (
    O365Notification,
    O365Notifications,
    O365NotificationsHandler
)

logger = logging.getLogger(__name__)


class O365StreamingNotification(O365Notification):
    """ O365 Streaming Notification """

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)


class O365StreamingNotifications(O365Notifications):
    """ O365 Streaming Notifications """

    _endpoints = {
        'subscriptions': '/subscriptions',
        'notifications': '/GetNotifications'
    }
    _request_type = '#Microsoft.OutlookServices.StreamingSubscription'
    streaming_notification_constructor = O365StreamingNotification

    # Streaming connection settings
    _default_connection_timeout_in_minutes = 120  # Equivalent to 2 hours
    _default_keep_alive_notification_interval_in_seconds = 5

    def __init__(self, *, parent=None, con=None, **kwargs):
        super().__init__(parent=parent, con=con, **kwargs)

    @property
    def request_type(self):
        return self._request_type

    @abstractmethod
    def resource_namespace(self, resource):
        """
        Get the full resource namespace for
        a given resource.

        :param resource: the subscribable resource
        :return the resource namespace
        """
        return resource

    def subscribe(self, *, resource):
        """
        Subscribing to a given resource.

        :param: resource: the resource to subscribe to
        :return: the subscription id
        """
        url = self.build_url(self._endpoints.get('subscriptions'))

        if resource not in self.subscribed_resources:
            self.subscribed_resources.append(resource)
        resource_namespace = self.resource_namespace(resource)

        data = {
            '@odata.type': self.request_type,
            self._cc('resource'): resource_namespace,
            self._cc('changeType'): self.change_type
        }

        try:
            response = self.con.post(url, data)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == requests.codes.too_many_requests:
                logger.warning('Too many requests...')
                logger.info(str(e.response.headers))
                logger.warning('Raising exception...')
                raise e
        else:
            if not response:
                return None

            notification = response.json()

            logger.debug("Subscribed to resource {0}: Response: {1}".format(resource, notification))
            return notification['Id']

    def create_event_channel(self, *, subscriptions, notification_handler=None,
                             connection_timeout=_default_connection_timeout_in_minutes,
                             keep_alive_interval=_default_keep_alive_notification_interval_in_seconds,
                             refresh_after_expire=False):
        """
        Create a new channel for events.

        :param subscriptions: subscription id's to listen to
        :param notification_handler: the notifications handler
        :param int connection_timeout: time in minutes in which connection closes
        :param int keep_alive_interval: time interval in seconds in which a message is sent
        :param bool refresh_after_expire: refresh when http connection expires
        """
        if not subscriptions:
            raise ValueError('Can\'t start streaming connection without subscription.')
        elif not isinstance(subscriptions, list):
            subscriptions = [subscriptions]

        notification_handler = notification_handler or O365NotificationsHandler()
        url = self.build_url(self._endpoints.get('notifications'))

        data = {
            self._cc('connectionTimeoutInMinutes'): connection_timeout,
            self._cc('keepAliveNotificationIntervalInSeconds'): keep_alive_interval,
            self._cc('subscriptionIds'): subscriptions
        }

        logger.info('Open new events channel ...')
        while True:
            try:
                response = self.con.post(url, data, stream=True)
                logger.debug('Start streaming cycle ...')

            # Renew subscriptions if 404 is raised
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == requests.codes.not_found:
                    logger.info('Expired subscription. Renewing subscriptions...')
                    data[self._cc('subscriptionIds')] = self.renew_subscriptions()
                    logger.info('Renewed subscriptions: {0}'.format(data[self._cc('subscriptionIds')]))
                    continue
                else:
                    raise e
            else:
                if not response:
                    return

            # Use 'with' clause to prevent requests.exceptions.ChunkedEncodingError.
            # Exception occurs when connection is closed by the server causing
            # partially reading the request body.
            with response:
                stream_data = b''
                bracket_control = []
                for starting_chunk in response.iter_content(chunk_size=1):
                    # Reading json group values...
                    if starting_chunk == b'[':
                        bracket_control.append(starting_chunk)
                        try:
                            for chunk in response.iter_content(chunk_size=1):
                                # Grouping json objects
                                if chunk == b'{':
                                    bracket_control.append(chunk)
                                elif chunk == b'}':
                                    bracket_control.remove(b'{')
                                elif chunk == b']':
                                    bracket_control.remove(b'[')

                                # Control to see if json object is complete
                                if b'{' in bracket_control:
                                    stream_data += chunk
                                elif b'[' in bracket_control:
                                    if stream_data:
                                        stream_data += b'}'
                                        notification = self.streaming_notification_constructor(
                                            parent=self, **json.loads(stream_data.decode('utf-8')))
                                        notification_handler.process(notification)
                                        stream_data = b''
                                else:
                                    # Break outer loop
                                    bracket_control.append(True)
                                    break  # Connection timed out

                        except Exception as e:
                            if isinstance(e, requests.exceptions.ChunkedEncodingError):
                                # Seem like empty values through the connection causing
                                # the communication to be corrupted. When that happens,
                                # the loop is interrupted and the streaming is restarted.
                                logger.warning("Exception suppressed: {0}".format(e))
                                break
                            else:
                                raise e
                    if bracket_control:
                        # Break loop since all data is read
                        break

            # Automatically refresh HTTP connection after it expires
            if refresh_after_expire:
                logger.debug('Refreshing connection ...')
            else:
                break

        logger.info('Stopped listening for events: connection closed.')
