# O365-notifications

__O365-notifications__ is a _pythonic_ implementation for the Notification services from Office 365. There are currently
2 ways for receiving notifications:
[Push Notifications](https://docs.microsoft.com/en-us/previous-versions/office/office-365-api/api/beta/notify-rest-operations-beta)
and
[Stream Notifications](https://docs.microsoft.com/en-us/previous-versions/office/office-365-api/api/beta/notify-streaming-rest-operations)
(beta only). For more details, see its documentation.

This approach is built on top of the current [O365](https://github.com/O365/python-o365) package. You are recommended to
look into its documentation for advance setups.

## Notification strategies

As mentioned, there currently 2 supported notification types in O365: _push_ and _streaming_.

As of now, this project relies on Outlook REST Beta API. But because this API is now deprecated and will be
decommissioned, a transition to Microsoft Graph API is required. See [this](#Important-note-⚠️) section for more
details.

### Push notifications

This project does not contain an implementation for this type of notification. Therefore, contributions are more than
welcome.

O365 documentation on push notifications can be
found [here](https://docs.microsoft.com/en-us/previous-versions/office/office-365-api/api/beta/notify-rest-operations-beta)
.

### Streaming notifications

This project provides an implementation for this type of notification. A quick example on how to use it is found below:

```python
import O365
import o365_notifications.base as base
import o365_notifications.streaming.mailbox as ms

account = O365.Account(...)
mailbox = account.mailbox()

# mailbox streaming for email creation events
mn = ms.O365MailBoxStreamingNotifications(
    parent=mailbox,
    change_type=base.O365Notification.ChangeType.CREATED.value
)

# get an inbox folder events subscription
subscription = mn.subscribe(resource=mailbox.inbox_folder())

# use default handler which simply logs out the arriving events
mn.create_event_channel(subscriptions=subscription)
```

O365 documentation on streaming notifications can be found
[here](https://docs.microsoft.com/en-us/previous-versions/office/office-365-api/api/beta/notify-streaming-rest-operations)
.

## Important note ⚠️

As communicated by
Microsoft [here](https://developer.microsoft.com/en-us/graph/blogs/outlook-rest-api-v2-0-deprecation-notice), The v2.0
REST endpoint will be fully decommissioned in November 2022, and the v2.0 documentation will be removed shortly
afterwards.

### What does it mean to this package?

#### Push notifications

Push notifications will be shifted to Microsoft Graph, and go under the name of _change notifications_. Its
documentation can be found [here](https://docs.microsoft.com/en-us/graph/api/resources/webhooks?view=graph-rest-1.0).

Transitioning to the Microsoft Graph should be a simple and straightforward task.

#### Streaming notifications

Unfortunately Microsoft will not port this service to Microsoft Graph. Therefore, as of November 2022, the current
implementation in this project will be obsolete. More details on that can be
found [here](https://docs.microsoft.com/en-us/outlook/rest/compare-graph).

## Requirements

See [requirements.txt](requirements.txt)

## License

[MIT](LICENSE)
