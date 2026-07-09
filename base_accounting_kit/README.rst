.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-19.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 19.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community-1ABC9C.svg
    :alt: Community Edition

.. |python| image:: https://img.shields.io/badge/Python-3.11-3776AB.svg
    :alt: Python 3.11

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |python| |maintainer|

Odoo 19 Accounting for Community
================================

Odoo 19 Full Accounting Kit brings full accounting features to Odoo 19
Community Edition. It adds advanced financial reports, complete asset
management, payment follow-ups, bank tools and much more — without any
Enterprise licence or per-user fees.

Key Features
------------

**Financial Reports (PDF & Excel)**

* Profit & Loss and Balance Sheet
* General Ledger and Trial Balance — with period-comparison columns
* Partner Ledger, Aged Receivable and Aged Payable
* Tax Report and Cash Flow Statement
* Bank Book, Cash Book and Day Book
* Journals Audit
* Every report is printable to PDF and exportable to Excel (XLSX)

**Asset Management**

* Asset categories with linear / degressive depreciation
* Auto-create assets directly from vendor bills
* Automated depreciation board with scheduled posting
* Pause & resume depreciation
* Asset revaluation (increase gross value mid-life)
* Asset disposal (sale / scrap) with automatic gain/loss

**Payment Follow-ups & Statements**

* Multi-level, automated payment follow-ups
* Follow-up emails and printable reminder letters
* Customer and vendor statements (print / Excel / email)
* Customer credit limit with warning and blocking stages

**Payments**

* Post-Dated Cheques (PDC) posted on their effective date
* Check printing with sequential numbering
* Bulk / batch payments
* Recurring customer invoices and vendor bills
* Recurring journal entries

**Bank & Reconciliation**

* Bank statement import (OFX / QIF / CSV / XLSX)
* Bank reconciliation widget
* Automatic bank matching (partner + amount, rule-based write-offs)
* Foreign-currency (FX) revaluation of open balances

**Other Tools**

* Multiple-invoice printing with custom layouts
* Accounting lock dates
* Account groups
* Multi-language translations

Installation
------------
This module uses the external Python packages ``openpyxl``, ``ofxparse``,
``qifparse`` and ``xlsxwriter``. Install them before installing the module::

    pip install openpyxl
    pip install ofxparse
    pip install qifparse
    pip install xlsxwriter

Configuration
-------------
No additional configuration is required. After installation, restart the Odoo
service and refresh the browser — the **Accounting** menu then appears in the
top navigation bar. Configure follow-up levels, asset categories and the
foreign-currency revaluation accounts from the Accounting settings.


Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
General Public License, Version 3 (LGPL v3).
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

