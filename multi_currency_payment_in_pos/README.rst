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

POS Multi Currency Payment
==========================
This module allows the use of multiple currencies in the Point of Sale module.

Key Features
------------
* **Multi-Currency per POS Configuration**: Enable multi-currency payment per Point of Sale and configure supported foreign currencies directly from settings.
* **Interactive Payment Screen Widget**: Toggle the multi-currency interface on demand during checkout with a clean, cashier-friendly interface.
* **Real-Time Exchange Rate Conversion**: Dynamically retrieves current currency conversion rates and displays converted order totals for the selected foreign currency.
* **Direct Foreign Amount Input**: Enter amounts directly in the customer's foreign currency and automatically generate base-currency payment lines.
* **Synchronized Payment Line Calculations**: Automatically updates and recalculates foreign currency amounts when payment lines or tender amounts are modified.
* **Multi-Currency POS Receipts**: Displays the paid foreign currency amount and currency code (e.g., INR) alongside the payment method on printed and digital POS order receipts.
* **Backend Order Tracking & Audit**: Stores foreign currency details (currency name and amount) on backend POS orders and payments for accounting reconciliation.

Installation
------------
No external dependencies.

Configuration
-------------
1. Navigate to **Point of Sale** -> **Configuration** -> **Settings**.
2. Under the **Multi-Currency** section, enable **Multi-Currency per Session**.
3. Select the supported foreign currencies in the **Currencies** field and click **Save**.

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
