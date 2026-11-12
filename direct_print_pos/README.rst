.. image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

Direct Pos Print
================
* Direct POS Print sends Odoo POS receipts straight to a PrintNode printer.

Configuration:
--------------
This module builds on the **Direct Print** module, so configure PrintNode there
first:

 * Install the PrintNode client from www.printnode.com/en/download for your
   operating system.
 * Create a PrintNode API key in your PrintNode account. The client connects
   the computers and printers associated with that account.
 * In **Settings → Direct Print**, enter your API key, check the available
   printers and select one or more printers.

Then, in **Settings → Point of Sale**, enable **POS Template**. When a cashier
prints a receipt, Odoo renders the POS receipt PDF and sends it to the selected
PrintNode printer.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
GNU Lesser General Public License, Version 3 (LGPL v3).
(https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------
Developer : (V19) Surya Gayathry TA , Contact: odoo@cybrosys.com
            (V18) Surya Gayathry TA , Contact: odoo@cybrosys.com

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
===================
HTML Description: `<static/description/index.html>`__
