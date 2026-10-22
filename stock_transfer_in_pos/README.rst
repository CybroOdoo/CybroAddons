.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community-1ABC9C.svg
    :alt: Community Edition

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |maintainer|

Point of Sale Stock Transfer
============================

This module helps to transfer stock from POS session.

Key Features
------------

* **POS Settings Integration**: Enable or disable stock transfer capability per POS configuration settings.
* **Direct Stock Transfer from POS**: Create stock transfers directly from the active Point of Sale screen using the "Stock Transfer" control button.
* **Automatic Line Items Mapping**: Automatically populates selected POS order line products and quantities into the transfer request.
* **Multiple Picking Type Support**: Select from available picking types (Internal Transfers, Delivery Orders, Receipts).
* **Flexible Transfer States**: Option to create transfers in **Draft**, **Ready** (Assigned/Reserved), or **Done** (Validated) state immediately from POS.
* **Direct Backend Link**: Displays a success popup with the generated stock picking reference and direct link to open the backend `stock.picking` form view.
* **Validation Guards**: Prevents transfer creation when no products are in the cart or when no picking type is selected.

Installation
------------
No external dependencies.

Configuration
-------------

1. Navigate to **Point of Sale -> Configuration -> Settings**.
2. Under the **Stock Transfer** section, enable the **Enable Stock Transfer** checkbox option.
3. Click **Save** to apply the configuration.
4. Open or resume a POS session; the **Stock Transfer** button will now be available in the control buttons area.

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

Bug Tracker
-----------
Bugs are tracked on GitHub Issues. In case of trouble, please check there if
your issue has already been reported.

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__

Further information
===================
HTML Description: `<static/description/index.html>`__
