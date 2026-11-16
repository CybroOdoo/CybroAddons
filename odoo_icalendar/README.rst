.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community-1ABC9C.svg
    :alt: Community Edition

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |maintainer|

Odoo iCalendar
==============

This module provides iCalendar (.ics) support in Odoo. Users can send event invitations with attached RFC 5545 compliant .ics files to attendees.

Key Features
------------

* Generate RFC 5545 compliant .ics files for calendar events.
* Send event invitations with attached .ics files directly to attendees.
* Compatible with Google Calendar, Microsoft Outlook, and Apple Calendar.
* Supports both standard timed events and all-day events.

Installation
------------
Requires python package vobject (pip install vobject).

Usage
-----
* Open any event in the Calendar application.
* Click the **Send ICS** button in the form view to email an .ics event invitation to attendees.
* In the Calendar list view, select multiple meetings and click **Send ICS File** from the Action dropdown menu to dispatch consolidated .ics files to each attendee.

Configuration
-------------
No additional configuration is required.

Credits
-------
* Cybrosys Techno Solutions <https://cybrosys.com/>

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Maintainer
----------
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__
