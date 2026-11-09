.. |license| image:: https://img.shields.io/badge/license-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community-1ABC9C.svg
    :alt: Community Edition

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |maintainer|

Sale Discount on Total Amount
=============================

This module is designed to manage discounts on the total amount in sales. It includes features to apply discounts either as a specific fixed amount or as a percentage, along with approval limits for discount controls.

Key Features
------------

* Apply discounts on the total amount of a sale order as a percentage or fixed amount.
* Automatic distribution and calculation of discount across sale order lines.
* Manager approval requirement if discount exceeds the configured limit.
* Seamless synchronization of total discount amounts to customer invoices.
* Display total discounts in quotation, sale order, and invoice PDF reports.

Installation
------------
No external dependencies.

Configuration
-------------
* Go to Sales -> Configuration -> Settings -> Pricing, enable "Sale Discount Approval" and set the discount limit in percentage.
* Sale orders whose discount exceeds the limit move to the "Waiting Approval" stage and must be approved by a Sales Manager.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Affero General Public License, Version 3 (AGPL v3).
(http://www.gnu.org/licenses/agpl-3.0-standalone.html)

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
