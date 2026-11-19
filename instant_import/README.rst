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

Instant Import
==============

Instant Import is a universal data import tool for Odoo that imports large
volumes of data into any Odoo model quickly and accurately from Excel or
CSV files. It reduces manual data entry and errors when importing
products, customers, vendors, invoices, inventory and more.

Key Features
------------

* Import records into any Odoo model.
* Supports XLSX, XLS and CSV files.
* Adds an Instant Import option to the actions menu of list views.
* Test the file before importing it.
* Handles many2one, many2many and one2many fields.
* Records are created through the Odoo ORM: access rights, defaults,
  sequences, computed fields and constraints apply as in a normal create.
* The whole file is imported at once and rolled back if any row fails.
* Creates activities for imported records from an activity column.

Installation
------------
No extra Python libraries are needed: files are read with Odoo's own import
readers (CSV, XLS, XLSX and ODS).

Configuration
-------------
No additional configuration is required.

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
