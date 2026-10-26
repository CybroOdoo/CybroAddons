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

Sales Order Double Approval
===========================

This module lets you require sales manager approval for sales orders above a
configured minimum amount. Orders at or below the threshold can be confirmed
directly by the salesperson.

Key Features
------------

* Two-step approval for sales orders.
* Set a minimum amount for manager approval.
* Sales managers can approve or cancel orders awaiting approval.
* Configure the minimum order amount that requires approval.

Installation
------------
 No external dependencies.

Configuration
-------------
Enable **Require Sales Manager Approval** on each applicable company form.
Then go to **Sales → Configuration → Settings**, select the threshold
currency, and set the minimum amount. Odoo converts that threshold to the order
company's currency before comparing it with the order total. Orders above the
threshold wait for a Sales Manager; orders at or below it follow the standard
confirmation flow.

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
