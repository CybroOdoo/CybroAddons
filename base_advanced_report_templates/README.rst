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

Odoo Professional Report Templates
==================================

Odoo Professional Report Templates provides modern, elegant, and fully customizable
PDF report designs for essential business documents across Sales, Purchase, Invoicing,
and Inventory management.

Key Features
------------

* **Four Distinct Themes**: Modern, Standard, Traditional, and Attractive visual templates for each document type.
* **Multi-Module Support**: Seamless styling for Sales Orders, Purchase Orders, Invoices/Credit Notes, and Delivery Slips.
* **Rich Color Customization**: Customize base background colors, heading text, body text, customer address text, and company address text.
* **Flexible Layout Positioning**: Configure company logo position, customer address position, and company address position (Left/Right).
* **Document Line Images**: Displays product line thumbnails on quotations, orders, invoices, and picking slips.
* **Customer Image Support**: Displays customer partner avatar on sales quotations and order documents.
* **Multi-Company Support**: Define distinct document layout preferences per company in a multi-company environment.
* **Interactive Document Preview**: Live QWeb document preview integrated within the document layout configuration wizard.
* **Graceful Fallback**: Custom or renamed themes render seamlessly using customizable templates without dropping back to unstyled reports.

Supported Documents
-------------------

1. **Sales Order / Quotation**: Custom PDF report (`base_advanced_report_templates.report_saleorder_custom`)
2. **Purchase Order / RFQ**: Custom PDF report (`base_advanced_report_templates.report_purchase_custom`)
3. **Invoices & Credit Notes**: Custom PDF report (`base_advanced_report_templates.report_invoice_custom`)
4. **Stock Delivery Slip**: Custom PDF report (`base_advanced_report_templates.report_deliveryslip_custom`)

Configuration
-------------

1. Go to **Settings > General Settings > Document Layout**.
2. Configure default layout themes for Sales, Purchase, Accounting, and Stock documents.
3. Access **Settings > Technical > Document Layout Themes** (or via company settings) to create or edit themes with custom palettes.
4. Save and print any quotation, purchase order, invoice, or delivery slip to view the styled PDF output.

Installation
------------

No external Python dependencies are required. Standard Odoo modules (`sale`, `account`, `stock`, `purchase`) are automatically utilized.

Company
-------

* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------

Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Contacts
--------

* Mail Contact: odoo@cybrosys.com
* Website: https://cybrosys.com

Maintainer
----------

.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__.
