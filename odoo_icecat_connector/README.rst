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

Odoo Icecat Connector
=====================

The Odoo Icecat Connector integrates the Icecat open catalogue database with your Odoo eCommerce website. Icecat is a world-leading provider of rich product content, providing access to millions of manufacturer-verified product datasheets, high-resolution imagery, detailed technical specifications, multimedia galleries, and documentation.

With this connector, you can automatically retrieve rich product datasheets and on-demand high-resolution images by simply providing the manufacturer Brand and Product Code (Internal Reference), providing customers with a rich, interactive shopping experience while keeping your Odoo database lightweight.

Key Features
------------

* Fetches rich product specifications, technical details, and descriptions directly from the Icecat catalog.
* On-demand download of high-resolution product images directly into Odoo via the "Fetch Icecat Image" button.
* Displays interactive product datasheets, user manuals, 3D tours, and multimedia galleries on eCommerce shop pages.
* Zero database bloat with client-side live media streaming and dynamic rendering.
* Simple configuration with Icecat User ID setup in Website Settings.
* Multi-company support with independent Icecat account configurations.

Installation
------------
No external dependencies.

Configuration
-------------
To configure the Icecat Connector:

1. Navigate to **Website > Configuration > Settings**.
2. Under the **Website Info** section, locate the **Icecat Connector** setting.
3. Enter your **Icecat User ID** (register at `Icecat <https://icecat.biz>`__ to get an Open Icecat account).
4. Click **Save**.

To display Icecat information on a product:

1. Navigate to **Website > Products > Products** (or **Inventory > Products > Products**).
2. Open the desired product template form view.
3. Specify the product's **Internal Reference** (matching the manufacturer part code on Icecat).
4. Enter the product **Brand**.
5. Click the **Fetch Icecat Image** button to fetch and save the high-resolution product image into Odoo.
6. Publish the product on your eCommerce website to display the live Icecat specifications, manuals, and multimedia.

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
