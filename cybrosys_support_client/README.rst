.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |maintainer|

Odoo Support Request
====================

Contact Cybrosys support without leaving Odoo. Open a request from the systray, describe the issue, attach files, and get a ticket reference back — or reach us on WhatsApp.

Key Features
------------

* Systray icon + user-menu entry, with an ``Alt+Shift+S`` keyboard shortcut.
* Transient wizard (``client.support``) – no data stored locally.
* Support type, category and priority selection.
* Multiple file attachments (sent inline, base64-encoded).
* Payload preview before sending.
* WhatsApp fallback channel.
* Robust, user-friendly error handling on submission.

Installation
------------
No external dependencies.

Configuration
-------------
The support server URL is stored in a system parameter, so a change of domain
is a config edit rather than a code release:

* **Settings → Technical → System Parameters**
* Key: ``cybrosys_support_client.endpoint_url``
* Default: ``https://support.cybrosys.com/help/request``

If the parameter is missing or blank, the module falls back to the default
above.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

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

