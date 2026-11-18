.. |license| image:: https://img.shields.io/badge/license-OPL--1-red.svg
    :target: https://www.odoo.com/documentation/master/legal/licenses.html#odoo-apps
    :alt: License: OPL-1

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community%20%26%20Enterprise-1ABC9C.svg
    :alt: Community and Enterprise Edition

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |maintainer|

Eagle Doc Connector
===================

Eagle Doc Connector integrates the Eagle Doc OCR and bookkeeping Partner API
with Odoo 20 to automate invoice and vendor bill processing.

Key Features
------------

* Upload PDF and image documents (PDF, PNG, JPG/JPEG) to Eagle Doc from the
  Invoices and Vendor Bills lists, one file or several at a time.
* Fill invoices and vendor bills automatically with the partner, reference,
  dates, currency, lines, taxes and discounts extracted by Eagle Doc.
* Warn about a total mismatch between the extracted total and the total
  computed by Odoo, both after extraction and again when the invoice is posted.
* Create customers or vendors, products and taxes found on a document, with
  one switch per item in the settings.
* Poll the processing status of pending uploads with a scheduled action.
* Synchronize customer and vendor master data to Eagle Doc from the contact
  form, from the list view action, or with a daily scheduled action.
* Create, refresh, update and delete the Eagle Doc sub-business linked to each
  company, including a batch creation action for several companies.
* Send vendor, bookkeeping account and tax code corrections back to Eagle Doc
  from the invoice.
* Check the monthly Eagle Doc usage from the settings.

Installation
------------

Install the Python package ``requests`` before installing the module:

::

    pip install requests

Then install *Eagle Doc Connector* from the Apps menu.

Configuration
-------------

Open *Settings > Eagle Doc Connector* and enter the Eagle Doc Base URL and API
Key. Optionally enable the auto-creation of customers/vendors, products and
taxes. When tax auto-creation is enabled, choose the placeholder sales and
purchase tax accounts.

Usage
-----

* Open *Accounting > Customers > Invoices* or *Vendors > Bills* and click
  *Upload to Eagle Doc*.
* Use *Correct Eagle Doc Extraction* on a draft document to send a correction.
* Use *Sync to Eagle Doc* on a customer or vendor to synchronize it.

Credits
-------

* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------

Odoo Proprietary License v1.0 (OPL-1)
(https://www.odoo.com/documentation/master/legal/licenses.html#odoo-apps)

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
