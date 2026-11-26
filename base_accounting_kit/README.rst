.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community-1ABC9C.svg
    :alt: Community Edition

.. |python| image:: https://img.shields.io/badge/Python-3.12-3776AB.svg
    :alt: Python 3.12

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |python| |maintainer|

Odoo 20 Accounting for Community
================================

Odoo 20 Full Accounting Kit brings full accounting features to Odoo 20
Community Edition. It adds advanced financial reports, complete asset
management, payment follow-ups, bank tools and much more — without any
Enterprise licence or per-user fees.

Key Features
------------

**Interactive Financial Reports (screen, PDF & Excel)**

* Profit & Loss and Balance Sheet (configurable structure)
* General Ledger and Trial Balance
* Partner Ledger, Aged Receivable and Aged Payable
* Tax Report and Cash Flow Statement
* Bank Book, Cash Book and Day Book
* Journals Audit
* Each report opens as a screen: date presets, comparison with several
  periods and variance, journal / partner / analytic / account filters,
  unfold lines, search, drill-down to the journal entry
* Saved filters per user, optionally opened by default
* PDF and Excel (XLSX) exports match the screen

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

* Bank statement import: CAMT.052 / .053 / .054, MT940, OFX, QIF, CSV and XLSX with saved column formats per journal
* Bank reconciliation screen: grouped by confidence, suggestions, partial matching, entry preview, early payment discount
* Automatic bank matching (partner + amount, rule-based write-offs)
* Open items matching: invoices against payments and credit notes, with write-offs
* Foreign-currency (FX) revaluation of open balances

**Other Tools**

* Multiple-invoice printing with custom layouts
* Closing menu: all five lock dates and lock date exceptions (reason, user, end, revoke)
* Fiscal years (e.g. a 15-month first year) followed by reports and numbering; close / reopen a year
* Year-end closing: checks, result moved to Retained Earnings, lock; reopen reverses it
* Month-end closing: automatic checks and closing tasks with responsible people, close and lock the month
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


Tests
-----
The module ships automated tests (``tests/``). Run them on an empty
database::

    odoo-bin -c <config> -d <new_db> -i base_accounting_kit --test-enable --test-tags /base_accounting_kit --stop-after-init

The browser tests need Google Chrome; skip them with
``--test-tags /base_accounting_kit,-kit_ui``.

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

