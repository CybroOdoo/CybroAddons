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

Odoo Drip Email Marketing
=========================

Automate the emails of your mailing lists. Send a welcome template to the
contacts who subscribe to a list, and a sequence of drip templates to all its
contacts, each a given number of days after the start date of the campaign,
through the chosen outgoing mail server. Every drip sent is logged in the drip
history of the mailing list and of the contact.

Key Features
------------

* Drip templates with a subject, a body and attachments, under Email Marketing
  > Configuration > Drip Templates
* Mail on subscription: the welcome template of a mailing list is sent to the
  contacts who join it, whether they are added from the list, imported or
  subscribe from the website
* Drip mass mailing: drip templates sent to all the contacts of a list a given
  number of days after its start date, until its end date
* One mail per contact, sent through the outgoing mail server of the list
* Contacts who opted out of the list or are blacklisted get no drip mail
* Drip History smart buttons on the mailing lists and the mailing contacts
* Works with both Community and Enterprise editions

Installation
------------
No external dependencies. The module depends on Email Marketing
(``mass_mailing``).

Configuration
-------------
Configure an outgoing mail server under Settings > Technical > Outgoing Mail
Servers, then select it in the Drip Mailing Configuration tab of the mailing
list.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

Credits
-------
* Developers: (V17) Nivedhya T, (V18) Busthana Shirin, (V19) Henna Mehjabin,
  (V20) Yadhu Shankar

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
