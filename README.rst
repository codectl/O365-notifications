******************
O365-notifications
******************

.. image:: https://img.shields.io/pypi/v/O365-notifications
    :target: https://pypi.org/project/O365-notifications
    :alt: PyPI version
.. image:: https://github.com/codectl/O365-notifications/actions/workflows/ci.yaml/badge.svg
    :target: https://github.com/codectl/O365-notifications/actions/workflows/ci.yaml
    :alt: CI
.. image:: https://codecov.io/gh/codectl/O365-notifications/branch/master/graph/badge.svg
    :target: https://app.codecov.io/gh/codectl/O365-notifications/branch/master
    :alt: codecov
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: code style: black
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: license: MIT

**O365-notifications** is a *pythonic* implementation for the Notification services
from Office 365. There are currently 2 ways for receiving notifications:

* `Push Notifications <https://docs.microsoft.com/en-us/previous-versions/office/
  office-365-api/api/beta/notify-rest-operations-beta>`__
* `Stream Notifications <https://docs.microsoft.com/en-us/previous-versions/office/
  office-365-api/api/beta/notify-streaming-rest-operations>`__

The versions on these are beta. For more details, see its documentation.

This approach is built on top of the current `O365 <https://github
.com/O365/python-o365>`__ package. You are recommended to look into its
documentation for advance setups.

Notification strategies
=======================
As mentioned, there currently 2 supported notification types in *O365*: **push** and
**streaming**.

As of now, this project relies on *Outlook REST Beta API*. But because this API is
now deprecated and will be decommissioned, a transition to *Microsoft Graph API* is
required. See `this <Important-note-⚠️>`__ section for more details.

Push notifications
------------------
This project does not contain an implementation for this type of notification.
Therefore, contributions are more than welcome.

*O365* documentation on push notifications can be found `here <https://docs.microsoft
.com/en-us/previous-versions/office/office-365-api/api/beta/notify-rest-operations
-beta>`__.

Streaming notifications
-----------------------
This project provides an implementation for this type of notification. A quick example
on how to use it is found below:

.. code-block:: python

    import O365
    from O365_notifications.base import O365NotificationHandler
    from O365_notifications.constants import O365EventType
    from O365_notifications.streaming import O365StreamingSubscriber

    account = O365.Account(...)
    mailbox = account.mailbox()

    # create a new streaming subscriber
    subscriber = O365StreamingSubscriber(parent=account)

    # ... and subscribe to resource events
    resource = mailbox.inbox_folder()
    events = [O365EventType.CREATED]
    subscriber.subscribe(resource=resource, events=events)

    # subscriber keeps track of active subscriptions
    assert len(subscriber.subscriptions) == 1

    # implement a notification handler for customized behavior
    subscriber.start_streaming(handler=O365NotificationHandler())

*O365* documentation on streaming notifications can be found `here <https://docs
.microsoft.com/en-us/previous-versions/office/office-365-api/api/beta/
notify-streaming-rest-operations>`__.

Important note ⚠️
=================
As communicated by *Microsoft* `here <https://developer.microsoft.com/en-us/graph/
blogs/outlook-rest-api-v2-0-deprecation-notice>`__, The ``v2.0`` REST endpoint will be
fully decommissioned in November 2022, and the ``v2.0`` documentation will be removed
shortly after.

What does it mean to this package?
----------------------------------
Let's see what it means for each one of the notification types:

Push notifications
^^^^^^^^^^^^^^^^^^
Push notifications will be moved to *Microsoft Graph*, and go under the name of
**change notifications**. Its documentation can be found `here <https://docs
.microsoft.com/en-us/graph/api/resources/webhooks?view=graph-rest-1.0)>`__.

Transitioning to the *Microsoft Graph* should be a simple and straightforward task.

Streaming notifications
^^^^^^^^^^^^^^^^^^^^^^^
Unfortunately *Microsoft* will not port this service to *Microsoft Graph*. Therefore, as
of November 2022, the current implementation in this project will be obsolete. More
details on that can be found `here <https://docs.microsoft.com/en-us/outlook/rest/
compare-graph>`__.

Tests & linting 🚥
===============
Run tests with ``tox``:

.. code-block:: bash

    # ensure tox is installed
    $ tox

Run linter only:

.. code-block:: bash

    $ tox -e lint

Optionally, run coverage as well with:

.. code-block:: bash

    $ tox -e coverage

License
=======
MIT licensed. See `LICENSE <LICENSE>`__.
