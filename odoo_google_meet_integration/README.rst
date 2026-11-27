.. |license| image:: https://img.shields.io/badge/license-OPL--1-red.svg
    :target: https://www.odoo.com/documentation/20.0/legal/licenses.html#odoo-apps
    :alt: License: OPL-1

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |maintainer|

Google Meet Calendar Integration
================================

Create Google Meet meetings straight from Odoo Calendar events. Tick the
Google Meet option on an event and the module creates the meeting in Google
Calendar, stores the meeting link and code on the event, and invites the
attendees.

Key Features
------------

* Connect a company to Google with its own OAuth Client ID and Client Secret
* Create a Google Meet link automatically when a calendar event is saved
* Join the meeting from the event with the Join Meeting button
* Invite the event attendees to the Google meeting by email
* Delete the meeting from Google Calendar by unticking Google Meet
* Refresh the access token from the company form

Installation
------------
Requires the ``requests`` Python library, which is installed with Odoo.

Configuration
-------------
Create OAuth credentials for the Google Calendar API in the Google Cloud
Console, then open Settings > Companies, pick the company and fill in the
Client ID, Client Secret and Authorized redirect URI on the Google Meet tab.
The redirect URI is your Odoo URL followed by ``/google_meet_authentication``.
Click Authenticate to connect the company.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Odoo Proprietary License v1.0 (OPL-1).
(https://www.odoo.com/documentation/20.0/legal/licenses.html#odoo-apps)

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com


This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__
