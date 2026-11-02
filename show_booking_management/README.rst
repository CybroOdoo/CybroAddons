.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
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

Show Booking Management
=======================
A module for show booking management. Administrators manage the shows and
users book them on the website by selecting the date, screen, time slot and seats.

Key Features
------------

* Admin manages shows: name, release date, type, language, poster, cast, time slots, screens and price.
* Users book a show on the website by selecting the date, screen, time slot and seats on a seating chart.
* Users can pre-book a show before its start date, within the pre-booking slots set by the admin.
* The booking is confirmed by paying the invoice; the ticket (with a QR code) is emailed and can be downloaded as a PDF.
* Users see their bookings under "Show Bookings" in the customer portal.

Installation
------------
No additional external dependencies (the ``qrcode`` Python library is part of Odoo's requirements).
A payment provider must be enabled to pay the booking invoices.

Configuration
-------------
Go to *Settings > Users* and give the users the *Show Booking Management*
rights: **Administrator** to manage shows, **User** to book shows.

**Who can book (Odoo 20).**
Booking on the website (*Show* menu) is reserved to logged-in users who have the
*Show Booking Management* User or Administrator right. Visitors are redirected
to the login page; portal customers and other users cannot book. Portal
customers only see their own bookings in *My Account > Show Bookings*.
Booking by portal customers is not supported.

**Paid bookings that cannot be confirmed.**
The ticket is issued when the invoice is fully paid. If the seats were taken in
the meantime, or the show was cancelled, the invoice is flagged, a note is
posted on it and the first Show Booking Management administrator gets an
activity. Find them with the *Movie Booking Needs Attention* filter on
invoices; the customer must be refunded or given other seats.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------
* Developer: (V17) Ashwin A,
             (V18) Rheshikes P K,
             (V19) Rheshikes P K,
             (V20) Abbas P

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : http://www.cybrosys.com

Bug Tracker
-----------
Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit https://www.cybrosys.com

Further information
===================
HTML Description: `<static/description/index.html>`__
