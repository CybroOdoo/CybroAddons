.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community-1ABC9C.svg
    :alt: Community Edition

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |maintainer|

Sales Team Access Controls
==========================

This module enforces role-based access control inside sales teams. Sales
Team Members can only view and manage the quotations, sales orders, CRM
leads and contacts they own, so their colleagues' records stay private.
Sales Team Leaders keep access to their own records and also see every
record of their sales teams, for supervision and performance tracking.

Key Features
------------

* Adds two groups: Team Member and Team Leader.
* Team Members see only the quotations, sales orders, order lines and
  leads where they are the Salesperson.
* Team Leaders also see the records of their sales teams and team members.
* Contacts are limited to the user's own customers, contacts they created,
  and customers on orders and leads they can see.
* Restrictions apply even when other apps, such as Inventory or Invoicing,
  grant wider access.
* Sales Administrators keep full access.

Installation
------------
No external dependencies.

Configuration
-------------
Assign users to the Team Member or Team Leader group in Settings > Users,
and add them to the right sales teams in Sales > Configuration > Sales
Teams.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

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
