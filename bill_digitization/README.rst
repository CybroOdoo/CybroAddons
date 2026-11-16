.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community-1ABC9C.svg
    :alt: Community Edition

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://www.cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |maintainer|

Bill Digitization
=================

Convert scanned paper bills and PDF documents (``.pdf``, ``.jpg``, ``.jpeg``, and ``.png``)
into editable draft vendor bills in Odoo 20 using Optical Character Recognition (OCR).

Key Features
------------

* Configurable activation from Accounting Settings (**Digitize Bill**).
* Dedicated **Digitize Bill** action button on the Vendor Bills list and kanban views.
* Extracts text via Tesseract OCR from image files and PDF pages (rendered via ``pdf2image``).
* Automatically creates a draft Vendor Bill populated with extracted Bill Reference, Bill Date,
  and matched or newly created product line items (quantity, unit price, and subtotal).
* Attaches the uploaded bill document directly to the generated Vendor Bill record.

Installation
------------

* Odoo module dependency: ``account``.
* Python dependencies: ``pytesseract``, ``pdf2image``, and ``pillow`` (``PIL``).
* System packages required on the server for live OCR processing: ``tesseract-ocr`` and
  ``poppler-utils``.

Configuration
-------------

Go to **Accounting -> Configuration -> Settings -> Vendor Bills** and enable
**Digitize Bill** so the **Digitize Bill** action button becomes available.

Usage
-----

1. Open **Accounting -> Vendors -> Bills**.
2. Click **Digitize Bill** on the Vendor Bills list or kanban view.
3. Upload a scanned vendor bill image (``.png``, ``.jpg``, ``.jpeg``) or PDF (``.pdf``)
   and click **Add**.
4. Review and confirm the newly created draft vendor bill and its attached source document.

Credits
-------

* Developer: (v20) `Cybrosys Techno Solutions <https://www.cybrosys.com>`__
* Contact: odoo@cybrosys.com

License
-------

LGPL-3

Maintainer
----------

.. image:: https://cybrosys.com/images/logo.png
   :target: https://www.cybrosys.com

This module is maintained by Cybrosys Technologies.
For support and more information, please visit https://www.cybrosys.com.

Further information
-------------------

* HTML Description: `static/description/index.html <static/description/index.html>`__
