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

Sale Stock Restrict
===================

Restrict the confirmation of sale orders when products are out of stock. Enable
the restriction from the Sales settings and choose whether stock is checked
against the on hand or the forecast quantity. Confirming an order that asks for
more than is available raises a warning that lists every product that is short.

Key Features
------------

* Enable or disable the out of stock restriction from the Sales settings
* Check stock against the On Hand Quantity or the Forecast Quantity
* The chosen quantity is shown as a column on the sale order lines
* Blocks sale order confirmation when stock is insufficient
* One warning message listing every product that is short, with quantities
* Only products that track inventory are checked; services and untracked goods
  are never blocked
* Units of measure are converted before comparing, so ordering in Dozens is
  checked correctly against stock kept in Units
* Website orders are not restricted
* Works with both Community and Enterprise editions

Installation
------------
No external dependencies. The module depends on Inventory (``sale_stock``) and
eCommerce (``website_sale``).

Configuration
-------------
Go to Sales > Configuration > Settings, enable *Out Of Stock Product
Restriction* under *Product Restriction*, and choose *On Hand Quantity* or
*Forecast Quantity* in *Based On*.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

Credits
-------
* Developers: (V17) Ashok P K, (V18) Raneesha M K, (V19) Vaishnav M V,
  (V20) Yadhu Shankar

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
