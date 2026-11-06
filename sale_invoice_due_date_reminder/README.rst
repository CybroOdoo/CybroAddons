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

Due Date Reminder for Invoicing and Sales
=========================================

Remind your customers before their payments are due. Set a due date on your
sale orders, and choose in the Sales and Invoicing settings how many days
before the due date the reminders are sent: a scheduled action emails the
customers of the sale orders that are not fully invoiced or paid, and of the
unpaid customer invoices, and logs each reminder on the document.

Key Features
------------

* Due Date on the sale orders
* Reminder for Sales: email the customers of the sale orders that are not
  fully invoiced or paid, a set number of days before their due date
* Reminder for Invoicing: email the customers of the unpaid customer invoices,
  a set number of days before their due date
* One reminder per due date, logged in the chatter of the document; a new due
  date gets a new reminder
* A reminder missed by the scheduled action is still sent while the due date
  is close
* Editable email templates in the language of the customer
* Works with both Community and Enterprise editions

Installation
------------
No external dependencies. The module depends on Sales (``sale_management``)
and Invoicing (``account``).

Configuration
-------------
* Sales > Configuration > Settings > Order Due Reminder: enable Reminder for
  Sales and set the number of days before the due date
* Invoicing > Configuration > Settings > Invoice Due Reminder: enable
  Reminder for Invoicing and set the number of days before the due date
* Set the Due Date on the sale orders

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

Credits
-------
* Developers: (V16) Amaya Aravind, (V17) Anjhana A K, (V18) Manasa T P,
  (V19) Gee Paul Joby, (V20) Yadhu Shankar

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
