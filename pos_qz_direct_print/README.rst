.. image:: https://img.shields.io/badge/license-LGPL--3-green.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

POS Direct Print
================
Send POS receipts silently and directly to any system printer — no browser print dialog, no IoT Box required.

Configuration
=============
- Download and install **QZ Tray** on the POS machine from `qz.io <https://qz.io/>`__ and keep it running.
- On the **Point of Sale** dashboard, open the POS configuration from the gear menu.
- On the **Configuration** tab, next to **Receipt Printers**, find **Direct Print (QZ Tray)**
- Enter your local computer's printer name in the **QZ Tray Printer Name** field (leave blank to use standard Odoo printing)
- Save and restart your POS session.

Configured Odoo receipt printers take priority. QZ Tray may prompt for approval
when connecting or printing unsigned jobs. If QZ Tray fails, Odoo uses the
browser print dialog when browser fallback is enabled.

Company
-------
* `Cybrosys Technologies Pvt. Ltd. <https://cybrosys.com/>`__

License
-------
GNU Lesser General Public License v3.0 (LGPL-3)
(https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------
* Developer: Fansa Jabeen A

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Bug Tracker
-----------
Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__

Further information
===================
HTML Description: `<static/description/index.html>`__
