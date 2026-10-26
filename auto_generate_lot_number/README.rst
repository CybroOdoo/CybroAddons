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

Auto Generate Serial/Lot Number
===============================

The Auto Generate Serial/Lot Number module automates the generation and assignment of unique serial and lot numbers for tracked products in Odoo 20. When confirming and validating purchase order receipts, it generates unique serial or lot numbers automatically—eliminating repetitive manual data entry.

The module provides both Global and Product-Wise configuration modes, allowing businesses to set standardized sequential prefixes and digit padding across the company or tailor numbering rules specifically for individual products.

Key Features
------------

* Automated Serial & Lot Generation: Automatically generates and assigns unique serial/lot numbers upon validating purchase order receipts.
* Dual Configuration Modes: Choose between Global configuration in Purchase Settings or individual Product-Wise numbering rules.
* Customizable Formatting: Define custom alphanumeric prefixes and specify digit padding counts for clear, consistent identification.

Installation
------------
No external dependencies.

Configuration
-------------
To configure global serial/lot numbering:

1. Navigate to **Purchase > Configuration > Settings**.
2. Locate the **Auto Generate Lot Number** section and enable **Auto Generate**.
3. Choose the **Global** option under **Serial/Lot Number**.
4. Enter the desired **Prefix** (e.g., ``LOT/`` or ``SN-``) and specify the number of **Digits** (e.g., ``5``).
5. Save settings.

To configure product-wise serial/lot numbering:

1. In **Purchase > Configuration > Settings**, select the **Product Wise** option under **Serial/Lot Number**.
2. Navigate to **Inventory > Products > Products** (or **Purchase > Products > Products**).
3. Open a tracked product form (with Traceability set to *By Unique Serial Number* or *By Lots* under the **Inventory** tab).
4. Under the **Traceability** section, specify the custom **Prefix** and **Digits** for that product.
5. Save the product.

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
Bugs are tracked on GitHub Issues. In case of trouble, please check there if
your issue has already been reported.

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__

Further information
===================
HTML Description: `<static/description/index.html>`__
