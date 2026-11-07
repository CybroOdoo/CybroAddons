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

Barcode scanning in Inventory
=============================

This module adds barcode scanning to inventory transfers. Scanning or
entering a product barcode on a transfer adds the product or increases
its quantity.

Key Features
------------

* Adds a Barcode field to the transfer form.
* Scanning a barcode increases the quantity of the matching product line
  by one.
* Adds a new line when the product is not yet on the transfer.
* Shows a warning when no product matches the scanned barcode.
* Adds a Barcode column to the operation lines; scanning a barcode there
  selects the product.

Installation
------------
No external dependencies.

Configuration
-------------
No additional configuration is required. Make sure your products have a
barcode set.

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
