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

Images in Excel File
====================
Export product images directly into Excel files as visual thumbnails instead
of raw Base64 strings. When exporting records with image fields (e.g.,
image_1920, image_128, avatar_128, photo, signature) from Odoo to XLSX format,
this module embeds the actual images inline so they are immediately visible
without any manual decoding.

Key Features
------------

* Embeds product images as thumbnails directly in XLSX cells.
* Supports all standard image field variants (image_1920, image_512, image_128, avatar_128, photo, signature).
* Converts image formats to PNG for full Excel compatibility.
* Auto-resizes rows and columns to fit thumbnails neatly.

Installation
------------
No external dependencies beyond standard Odoo Python packages (Pillow, xlsxwriter).

Configuration
=============
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

