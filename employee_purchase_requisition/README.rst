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

Employee Purchase Requisition
=============================

This module lets employees create material requisition requests, which go
through multi-level approval by the requisition manager and the department
head. Approved requisitions generate purchase orders and internal
transfers, and a PDF report can be printed for each requisition.

Key Features
------------

* Employees create requisitions with one or more products, choosing
  Purchase Order or Internal Transfer for each line.
* Two approval levels: Department Approval by a Requisition Manager, then
  Head Approval by a Department Head.
* The same user cannot approve at both levels.
* Choose a vendor for each purchase line before approval.
* Creates one purchase order per vendor and internal transfers for stock
  lines.
* Set default source and destination stock locations on departments and
  employees.
* Smart buttons to open the related purchase orders and internal transfers.
* Print a PDF report for each requisition.
* Three access groups: Requisition Users, Requisition Manager and
  Department Head.

Installation
------------
No external dependencies.

Configuration
-------------
Assign users to the Requisition Users, Requisition Manager or Department
Head group in Settings > Users. Optionally set a stock location on
departments and employees to use as the default source and destination of
internal transfers.

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
