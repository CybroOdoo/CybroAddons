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

Import Dashboard
================

Import Dashboard gives you one place to bulk import sale orders, purchase orders, invoices, payments, POS orders, products, partners, pricelists, bills of materials, tasks and attendances from CSV or Excel files, with a downloadable sample template for each import type.

Key Features
------------

* **Centralized Import Dashboard:** Single unified interface in Odoo to manage and execute bulk imports across all major business operations.
* **Dual Format Support:** Full support for both CSV and Excel (.xlsx) file formats with sample template downloads for each import type.
* **Sale Order Import:**
    - Bulk import quotations and sales orders with multi-line items.
    - Match products by Name, Internal Reference, or Barcode.
    - Supports order numbering from file or system sequence.
    - Option to automatically confirm quotations upon import.
* **Purchase Order Import:**
    - Bulk import Requests for Quotation (RFQs) and purchase orders.
    - Match products by Name, Internal Reference, or Barcode.
    - Automatic vendor tax assignment and planned delivery dates.
    - Option to automatically confirm purchase orders.
* **Invoice & Vendor Bill Import:**
    - Import Customer Invoices, Vendor Bills, Credit Notes, and Refunds.
    - Support for multiple product variants, line discounts, taxes, and payment references.
    - Auto-post invoices and optionally update posted records.
* **Customer & Vendor (Partner) Import:**
    - Import contacts and companies with complete address details, contact info, tags, and salesperson.
    - Methods: Create New or Create & Update existing records.
    - Flexible update criteria: match by Name, Email, or Phone.
* **Product & Variant Import:**
    - Import product templates and variants with sales price, cost price, categories, UoM, barcode, and internal reference.
    - Auto-creates product categories and units of measure if not already present.
* **Pricelist Imports:**
    - Customer Pricelist rules import (fixed price, discount, or formula).
    - Vendor Pricelist rules import with minimum quantities and validity dates.
* **Bills of Materials (BoM) Import:**
    - Import manufacturing BoMs and Kits with components and quantities.
* **POS Orders Import:**
    - Import Point of Sale orders with session, customer, product lines, and payments.
* **HR Attendance Import:**
    - Import employee check-in and check-out attendance records.
* **Customer & Vendor Payment Import:**
    - Bulk import accounting payments with journal, payment method, partner, and amounts.
* **Project Tasks Import:**
    - Import project tasks with assigned users, project, deadlines, and descriptions.
* **Configurable Dashboard Cards:**
    - Settings toggles in Odoo configuration to show or hide specific importer cards based on installed apps and business requirements.
* **Data Validation & Reporting:**
    - Comprehensive data validation with detailed row-by-row import summaries, error logs, and warnings.

Installation
------------
No external dependencies.

Configuration
-------------
Install the apps you want to import data into, then enable the matching import options in Settings > Import Dashboard.

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

