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

Chatter Attachment Manager
==========================

Chatter Attachment Manager enhances attachment handling across Odoo 20. It empowers users to easily manage, edit, download, and preview attachments directly within the chatter and discuss views of any record.

Key Features
------------
* Download all attachments on any record as a single `.zip` file.
* Direct upload options: local device files, live webcam snapshot capture, and screen recording.
* Attachment context menu on every file card with options to edit record metadata, launch image editor, preview offline, generate QR code, or delete.
* Integrated TUI Image Editor to crop, annotate, apply filters, and adjust images inside Odoo.
* Offline preview for spreadsheets (`.xlsx`/`.xls`), documents (`.docx`), and PDFs.
* Dynamic QR Code generation for instant mobile download of attachments.
* Categorize attachments with custom color tags and filter/group by tags in search view.

Installation
------------
External Python dependencies required:

* qrcode (install via ``pip install qrcode``)
* python-docx (optional, for docx preview: ``pip install python-docx``)

Configuration
-------------
No additional configuration is required.

Usage
-----
1. Open any record with a chatter view (such as Contacts, Sales Orders, or Invoices).
2. Use the chatter attachment upload dropdown to select files from your device, take a picture with the front camera, or record your screen.
3. On any uploaded attachment card, click the three-dot action button to open options:
   * **Edit Record**: Open the attachment form view to assign tags or edit file metadata.
   * **Image Editor**: Launch the built-in image editor to crop, annotate, and save changes directly.
   * **Preview Offline**: Preview document and spreadsheet contents directly within the browser without external viewers.
   * **QR Code**: Generate and print a QR code report enabling mobile users to download the file directly.
   * **Delete**: Remove the attachment with standard access rights verification.
4. Click the download icon in the attachment control panel to download all attachments for the record in a single `.zip` archive.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------
* Cybrosys Techno Solutions

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Maintainer
----------
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__
