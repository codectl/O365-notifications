# Push Notifications service for Office 365 API

__O365-subscription__ is a pythonic implementation for the Push Notification service from Office 365. There are currently 2 ways for receiving notifications: [Push Notifications](https://docs.microsoft.com/en-us/previous-versions/office/office-365-api/api/beta/notify-rest-operations-beta) and [Stream Notifications](https://docs.microsoft.com/en-us/previous-versions/office/office-365-api/api/beta/notify-streaming-rest-operations) (beta only). For more details, see its documentation.

This approach is built on top of the current [O365](https://github.com/O365/python-o365). You are recommended to look into its documentation for advance setups.

## Install

Requirements: >= Python 3.4

Project dependencies installed by pip:

* requests
* requests-oauthlib
* beatifulsoup4
* stringcase
* python-dateutil
* tzlocal
* pytz
* SQLAlchemy
* manage.py (local dependency)
