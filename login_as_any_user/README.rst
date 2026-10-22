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


Login As Any User
=================

The Login As Any User module lets administrators switch to any user account
without that user's password. Administrators can then see and test Odoo
exactly as that user does, and switch back to their own account with one click.

Key Features
------------

* Adds a **Switch User** button to the systray of the backend.
* Administrators can pick any other user from a wizard and log in as that user
  without a password.
* The wizard shows the selected user's access groups before switching.
* Clicking the same systray button while logged in as another user switches
  back to the original administrator account.
* Switching back is allowed only when the original account is still an
  administrator.
* Honours two-factor authentication: if the target user has 2FA enabled, the
  session is not finalized until 2FA is completed.

Usage
-----

#. Log in as an administrator.
#. Click the **Switch User** (person) icon in the systray.
#. Select the user to log in as. The user's access groups are listed below.
#. Click **Switch User**. The page reloads and you are logged in as the
   selected user.
#. To return to your administrator account, click the same systray icon again.

Installation
------------
No external dependencies.

Configuration
-------------
No additional configuration is required.

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

