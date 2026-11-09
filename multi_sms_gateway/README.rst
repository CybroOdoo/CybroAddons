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

Multiple SMS Gateway Integration
================================
Module for sending SMS through different SMS gateways such as Twilio, TeleSign, and Vonage.


Key Features
------------
* **Multi-Gateway Integration**: Connect and send SMS through Twilio, Vonage, and TeleSign using individual API credentials.
* **Direct Contact Integration**: Dispatch SMS directly from Contact form and list views via the "Send SMS via Gateway" action.
* **Bulk SMS Dispatch**: Send batch SMS messages to multiple selected contacts in a single operation.
* **Partner Chatter Logging**: Automatically logs sent SMS messages directly into the contact's communication chatter.
* **Centralized SMS History**: Complete audit trail tracking dispatched messages with gateway provider, dispatch date, recipient numbers, and message content.
* **No Odoo IAP Required**: Uses your own gateway account and direct API credentials without requiring Odoo IAP credits.


Installation
------------
- Refer to `Odoo Installation Documentation <https://www.odoo.com/documentation/20.0/administration/on_premises.html>`__
- Install required Python dependencies:

.. code-block:: bash

    pip install telesign twilio vonage

- Place the ``multi_sms_gateway`` module into your custom addons directory and update the Apps list.
- Install the **Multiple SMS Gateway Integration** module.


Configuration
-------------
1. Assign the user to the security group **Multiple SMS Gateway / Manager** under **Settings > Users & Companies > Users**.
2. Navigate to **SMS Gateway > Gateway List**.
3. Select and configure your desired SMS gateway provider:
   * **Twilio**: Provide Account SID, Auth Token, and Twilio Phone Number.
   * **TeleSign**: Provide Customer ID and API Key.
   * **Vonage**: Provide API Key and API Secret.

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
