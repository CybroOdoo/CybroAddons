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

=====================
Mailercloud Connector
=====================

Mailercloud Connector seamlessly integrates your Odoo ERP with Mailercloud, a leading email marketing platform. Effortlessly synchronize your contacts, map custom attributes, manage mailing lists, and keep customer data synchronized in real time.

Features
========

* **Secure API Integration**: Connect to Mailercloud using your API key with a built-in connection tester. Configuration access is securely restricted to Administrators.
* **Account & Quota Overview**: View plan details, active status, contact quotas (total, used, remaining), and last synchronization timestamp directly in Odoo.
* **Mailing List Management**: Automatically retrieve and manage your Mailercloud mailing lists from Odoo.
* **Custom Property Mapping**: Map standard and custom Odoo partner fields (Name, Email, Phone, etc.) to Mailercloud properties.
* **Batch Contact Synchronization**: Export all existing Odoo contacts to your designated Mailercloud list in efficient batches.
* **Real-Time Contact Synchronization**: Automatically create and update contacts in Mailercloud whenever partners are added or modified in Odoo.
* **Safe Sync Execution**: Non-blocking error handling ensures partner creation and edits in Odoo succeed even when Mailercloud is unreachable or encounters network issues.

Configuration
=============

1. **Obtain Mailercloud API Key**:
   * Log in to your Mailercloud account at https://app.mailercloud.com.
   * Navigate to **Account -> Integrations -> API Keys**.
   * Create or copy an API key.

2. **Configure in Odoo**:
   * Navigate to **Mailercloud Connector -> Configuration**.
   * Paste your Mailercloud API key in the **API Key** field.
   * Click **Test Connection** to authenticate and load account details, mailing lists, and default contact properties.

3. **Field Mapping & Contact Sync**:
   * In the **Contact Sync** notebook tab, select your target **Mailing List**.
   * Configure the field mapping between Mailercloud properties and Odoo partner fields.
   * Click **Sync Contacts** to perform the initial batch synchronization of contacts to Mailercloud.
   * Once synced, subsequent partner creations and field edits will automatically synchronize to Mailercloud.

Security
========

* API key and configuration settings are restricted to users with the **Administration / Setting** group (``base.group_system``).
* Standard employees without system administration permissions cannot view or edit credentials.
* Contact synchronization utilizes elevated execution context internally to allow standard users to manage partners without exposure to API credentials.

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
