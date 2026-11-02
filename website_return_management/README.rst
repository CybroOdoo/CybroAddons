.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
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

Website Return Order Management
================================
This module allows customers to request the return of a website/sale
order from their customer portal, and lets internal users track and
process those return requests against the original delivery.

Key Features
------------

* Customers can request a return for a product on a confirmed sale order from the website/portal.
* Return requests are tracked as their own "Sale Return" records, with a Draft / Confirm / Done / Cancel status.
* Confirming a return creates a linked, scoped return transfer for just the requested product and quantity.
* A "Return Orders" page and badge counter are available in the customer portal, and a return-order smart button is added to Sales Orders.
* A dedicated PDF report is available for each return order.

Installation
------------
No external dependencies.

Configuration
-------------
No additional configuration is required for this module.

**Note - Odoo's own "Allow Spontaneous Returns" setting.**
Odoo 20 (``sale_stock``) has a built-in customer return feature that is switched
off by default: *Settings > Inventory > Operations > Allow Spontaneous Returns*.
If a company turns it on, the portal Sales Order page shows **two "Return"
buttons** for orders delivered within the configured number of days:

* Odoo's own button in the order sidebar. It opens a dialog where the customer
  picks products, quantities and a reason and downloads a return label (PDF).
  It only posts a note on the sale order; it does not create a return order or
  a return transfer.
* This module's button in the order header. It creates a tracked Return Order
  (Sales > Return Orders) that staff confirm to create the return transfer.

The two flows are independent. To offer only this module's return flow, leave
*Allow Spontaneous Returns* disabled (the default).

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------
Developer:  (V14) Shijin V,
            (V15) Rosmy,
            (V16) Rosmy,
            (V17) Ammu Raj,
            (V18) Sruthi C Nair,
            (V19) Henna Mehjabin,
            (V20) Abbas P,

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Bug Tracker
-----------
Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__

Further information
====================
HTML Description: `<static/description/index.html>`__
