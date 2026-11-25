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

Odoo Zendesk Connector
======================

Seamlessly integrate Odoo Helpdesk with Zendesk to synchronize customer support
tickets. Create, update, and delete tickets directly from Odoo, and import or export
tickets between both platforms.

Key Features
------------

* Bi-directional synchronization of support tickets between Odoo and Zendesk
* Create tickets in Zendesk directly from Odoo Helpdesk tickets
* Update linked Zendesk tickets with latest subject, description, and status changes
* Delete or unlink tickets from Zendesk with automatic status cleanup
* Import tickets from Zendesk within a selectable date range with pagination support
* Export existing Odoo Helpdesk tickets to Zendesk within specified date intervals
* Automatic customer/requester matching and creation based on contact email
* Mapping of ticket priority levels between Odoo and Zendesk
* Secure OAuth 2.0 authentication (Client Credentials grant) with token caching
* Built-in connection test tool to verify API credentials
* Works with both Community and Enterprise editions

Installation
------------
The module depends on Website Helpdesk (``odoo_website_helpdesk``) and Mail (``mail``).
Ensure the ``odoo_website_helpdesk`` module is installed and available in your addons path.

Configuration
-------------
* Go to **Settings > Helpdesk > Connect Zendesk**:
  * Enable **Connect Zendesk**
  * Enter your **Company Domain** (e.g. ``mycompany`` for ``https://mycompany.zendesk.com``)
  * Enter your **OAuth Client Identifier** created in Zendesk Admin Center
  * Enter your **OAuth Client Secret**
  * Enter the **OAuth Scope** (default: ``read write``)
* Click **Test Connection** to verify your Zendesk credentials and connectivity
* Go to **Helpdesk > Configuration > Import/Export Tickets** to import or export tickets

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
