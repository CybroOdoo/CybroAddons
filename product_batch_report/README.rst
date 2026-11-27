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

Lot and Serial Number Expiry Report
===================================

Print a PDF report of the lots and serial numbers that have expired or are
going to expire. Only lots with a quantity on hand are listed.

Key Features
------------

* Report by lot or serial number, or grouped by product.
* List expired lots or lots that are going to expire.
* Limit the report to a number of days counted from today.
* Select the products to include when the report is grouped by product.

Installation
------------

No external dependencies. The module depends on the Inventory
(``stock``) and Expiration Dates (``product_expiry``) apps.

Configuration
-------------

#. Enable **Lots & Serial Numbers** under **Inventory > Configuration >
   Settings**. The **Expiration Dates** setting only appears after that.
#. Make sure **Expiration Dates** is enabled in the same screen.
#. Turn on **Expiration Date** on the products you track.

Usage
-----

#. Open **Inventory > Reporting > Lot/Serial Expiry**.
#. Choose **Lot/Serial Wise** or **Product Wise** in **Tracking**.
#. Choose **Expired** or **Going to Expire** in **Tracking Type**.
#. Optionally set the number of days in **Within**, and the products.
#. Click **PDF Report**.

The menu and the wizard are available to users in the Inventory Administrator group.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------
* Cybrosys Techno Solutions <https://www.cybrosys.com>

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
