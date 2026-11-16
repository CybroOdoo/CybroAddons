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

POS Custom Tips
===============

Apply fixed percentage tips effortlessly in Odoo 20 Point of Sale. Configure custom tip percentages per POS terminal, add tips with one click on the payment screen, and ensure seamless sync with customer receipts and backend order records.


Key Features
------------

* **Configurable Tip Percentage**: Define a default custom tip percentage per POS terminal or shop in Point of Sale settings.
* **Dynamic Payment Screen Button**: Automatically displays a dedicated button (e.g., ``Tip (10%)``) on the POS payment screen matching your configured percentage.
* **1-Click Tip Pre-fill & Confirmation**: Opens the native Add Tip number keypad with the preset percentage pre-selected for fast, one-touch confirmation.
* **Flexible Amount ($) and Percent (%) Support**: Cashiers can easily adjust the percentage or switch to a flat currency tip amount on the keypad before confirming.
* **Real-Time Total Calculation**: Instantly calculates the tip amount from the order lines and updates the total payable amount in real-time.
* **Itemized Customer Receipts**: Displays the tip as an explicit line item on printed and digital customer tickets with full tax and subtotal breakdown.
* **Backend Order Audit & Accounting Sync**: Records tip products as separate line items on backend POS orders, synchronizing cleanly with session reports and journal entries.
* **Native Odoo 20 OWL Integration**: Developed using modern Odoo 20 OWL components for optimal responsiveness and smooth checkout experience.


Installation
------------
No external dependencies are required.


Configuration
-------------
1. Navigate to **Point of Sale > Configuration > Settings**.
2. Under the **Payment** section, enable **Tips** and select a **Tip Product**.
3. Set your preferred tip percentage in the **Add % tip** field.
4. Click **Save**. When opening a POS session, the custom tip percentage button will appear on the payment screen.


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
