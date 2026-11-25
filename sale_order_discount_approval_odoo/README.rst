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

Sale Order Discount Approval
============================

Enforce discount governance and management approval for sales orders in Odoo 20.
When sales discounts on quotation lines or global orders exceed the configured
maximum allowed discount limit for a user, the order is automatically held in
a 'Waiting For Approval' state without early confirmation, and approval notifications
are dispatched to designated Discount Approval Managers.

Key Features
------------

* Configure per-user discount control with customized maximum allowed discount limits.
* Automatic transition of quotations to 'Waiting For Approval' state when limits are exceeded.
* Prevents order confirmation, delivery creation, and stock reservation until approved.
* Automated email notifications sent directly to users in the Discount Approval Manager group.
* Dedicated 'Approve' action button for Discount Approval Managers to confirm held orders.
* Complete audit trail recording the approving manager and approval activities in the chatter log.
* Seamless validation for both individual line-item discounts and global order discounts.

Installation
------------

No external dependencies. Works directly with the standard Odoo 20 Sales (sale_management) module.

Configuration
-------------

1. Navigate to Settings -> Users & Companies -> Users, select a salesperson, and open the 'Discount Control' tab.
2. Enable 'Discount Control' and specify the 'Allowed Discount (%)' threshold for the salesperson.
3. For users who should review and approve orders, assign them to the 'Sale Order Discount Approval / Discount Approval Manager' security group.

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
----------

.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com


This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__.
