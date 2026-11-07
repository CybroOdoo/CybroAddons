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

MRP Substitutes Products
========================

Add substitute products directly to Bill of Materials (BOM) components. When primary components are unavailable during manufacturing order confirmation, the system automatically swaps them with configured substitutes.

Key Features
------------

* BOM-Level Substitute Mapping: Configure fallback products directly on BOM component lines.
* Automated MO Substitution: Automatically swap out-of-stock components with designated substitute items upon manufacturing order confirmation.
* Free Stock Aware: Evaluates net free stock (on-hand minus reservations) to accurately identify real component depletion.
* Role-Based Access Control: Manage configuration visibility via the dedicated 'Allow Substitute Product (MRP)' security privilege.
* Uninterrupted Production: Prevents shop floor halts and bottlenecks without manual recalculation.

Installation
------------
No external dependencies. Works out of the box with the standard Odoo 20 Manufacturing (mrp) module.

Configuration
-------------
* Navigate to Settings -> Users & Companies -> Users.
* Select the user and locate the 'Other' section.
* Enable the 'Allow Substitute Product (MRP)' privilege to grant access to substitute product configuration on BOM lines.

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
