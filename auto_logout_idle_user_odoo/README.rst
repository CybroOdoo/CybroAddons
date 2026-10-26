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

Logout Idle User
================

Automatically log out idle users after a configured inactivity period.

Key Features
------------

* Automatically log out idle users after configured idle time (detected in the browser)
* User-specific idle duration configurable in user profile
* Systray countdown timer displaying remaining session time

Installation
------------
No external dependencies.

Configuration
-------------
Go to Settings > Users & Companies > Users, open a user, enable the idle timeout and set the idle duration in minutes (default 15, minimum 1). The systray shows a countdown of the remaining time. When the user's browser sees no mouse, keyboard or touch activity for that period, the session is logged out.

Note: the timeout is enforced by the user's browser (all open tabs share the activity); it is not a server-side session expiry.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------
Developers: (V16) Yadhukrishnan, (V17) Anurudh P, (V18) Ranjith R, (V19) Swaraj R, (V20) Arjun P P

Contact: odoo@cybrosys.com

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Bug Tracker
-----------
For bugs or support, please contact odoo@cybrosys.com.

Maintainer
----------
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com


This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__

Further information
-------------------
HTML Description: `<static/description/index.html>`__
