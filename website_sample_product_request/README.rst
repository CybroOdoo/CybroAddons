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

Website Sample Product Request
==============================

This module allows customers to request product samples from the website
and tracks the resulting sample orders in the backend.

Key Features
------------

* Mark products as sample products from the product form.
* Browse and request sample products on a dedicated website shop page
  (``/shop?type=sample``).
* Sample product orders are priced at zero and flagged as sample orders
  in the Sales backend.
* View all sample products under **Sample** > **Sample Products** and
  all sample orders under **Sample** > **Sample Order**.

Installation
------------
No external Python dependencies are required.

Configuration
-------------
Open any product form and enable the **Is Sample Product** checkbox.
The product will then appear on the website sample shop page and its
price will be set to zero on checkout.

Usage
-----
1. In the backend, go to **Sales** > **Sample** > **Sample Products** and
   enable **Is Sample Product** on the desired products.
2. On the website, navigate to the sample shop page at ``/shop?type=sample``.
3. Add a sample product to the cart and complete the order; the price is
   recorded as zero and the order is flagged as a sample order.
4. Review submitted sample orders under **Sales** > **Sample** >
   **Sample Order**.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------
* Developer: Cybrosys Techno Solutions

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

