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

=====================
One2many Excel Report
=====================
This module provides an interactive widget (``one2many_excel``) that allows users to export the contents of any One2many line field directly into a formatted Excel (.xlsx) file.

Key Features
------------
* Available for Odoo 20.0 Community and Enterprise editions.
* Exports One2many lines to formatted Excel spreadsheets directly from form views.
* Automatically inspects active list views to determine column headers and field order.
* Formats dates, numbers, relational fields, and multi-line descriptions cleanly.

Installation
------------
No external dependencies are required. Standard ``xlsxwriter`` is used for spreadsheet generation.

Configuration
-------------
To enable Excel export on a One2many field in any view, set the
``widget="one2many_excel"`` attribute on the field in the view XML definition:

.. code-block:: xml

    <field name="order_line" widget="one2many_excel"/>

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Contacts
--------
* Email: odoo@cybrosys.com
* Website: https://cybrosys.com

Maintainer
----------
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__.
