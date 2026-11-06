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

Website GDPR In Odoo
====================

Lets your customers request a copy or the deletion of their personal data
from the customer portal, as required by the General Data Protection
Regulation (GDPR). The website administrator approves or cancels each
request; an approved download gives the customer a PDF of their data, and an
approved deletion clears the selected fields of the customer contact.

Key Features
------------

* GDPR templates: choose the contact fields that customers can download or delete.
* Personal Data card and page in the customer portal.
* Download requests: the customer downloads a PDF of their data once the request is approved.
* Delete requests, confirmed by the customer in a dialog; approving one clears the template fields of the contact.
* No duplicate requests: a request that is already pending is not created again.
* The customer follows the status of each request in the Your Requests tab.
* Optional email to the customer when a request is approved or cancelled.

Installation
------------
No external dependencies. Requires the Website, Portal and Contacts modules.

Configuration
-------------
Create the templates in Website > Configuration > GDPR > GDPR Templates. The
requests are processed in Website > Configuration > GDPR > GDPR Requests by
the website administrators.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------
* Developers: (V20) Nivedhya T, Yadhu Shankar
  Contact: odoo@cybrosys.com

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
