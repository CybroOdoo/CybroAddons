.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-19.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 19.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community-1ABC9C.svg
    :alt: Community Edition

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |maintainer|

Posted Invoices to Draft in Bulk
================================

Reset (or cancel) many posted invoices, bills and credit notes at once — straight
from the invoice list view's **Action** menu. The module reuses Odoo's own
reset-to-draft / cancel logic and processes each record safely, so a single
locked or ineligible record never blocks the whole batch.

Features
--------

* **Bulk Reset to Draft** — select multiple posted invoices/bills/refunds and
  reset them all to Draft from the list Action menu.
* **Bulk Cancel** — a matching "Cancel (Bulk)" action sets many invoices to
  Cancelled in one click.
* **Smart skip & summary** — ineligible records (not posted, locked/hashed
  periods, tax cash-basis, records needing a cancellation request, …) are
  skipped and reported; the batch never fails as a whole.
* **Reason in the chatter** — add an optional reason that is logged in every
  affected invoice's chatter for a clean audit trail.
* **Standard Odoo logic** — reuses core ``button_draft()`` / ``button_cancel()``,
  processed per record inside savepoints.
* **Manager-only** — restricted to the Accounting Manager group.

Configuration
-------------
No configuration is required. After installation, an Accounting Manager will see
**Reset to Draft (Bulk)** and **Cancel (Bulk)** in the Action menu of the
invoice / bill list views.

Installation
------------
This module depends on **base_accounting_kit** (Full Accounting Kit); installing
it will pull that in automatically. No extra Python packages are required.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
General Public License, Version 3 (LGPL v3).
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
