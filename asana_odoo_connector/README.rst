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

Asana Odoo Connector
====================

The **Asana Odoo Connector** module enables seamless integration and project/task synchronization between Odoo 20 and Asana.

Keep your project management workflows and teams in sync across platforms. Projects and tasks can be fetched from your Asana workspace into Odoo or exported from Odoo into Asana with accurate hierarchy and stage placement.

Key Features
------------

* **Project & Task Integration:** Connect and synchronize projects, stages, and tasks between Odoo and Asana.
* **One-Click Project Import:** Import projects, stages, and tasks from your designated Asana workspace directly from Odoo Settings with automatic deduplication.
* **List View Export Action:** Select projects from the Odoo Projects tree/list view and export them along with their stages and tasks to Asana via the Action menu.
* **Instant Connection Verification:** Built-in connection test tool validates Personal Access Tokens (PAT) and Workspace IDs with immediate user feedback.

Installation
------------

This module requires the official Asana Python SDK library. Install it in your Odoo Python environment before installing the module:

.. code-block:: bash

    pip install asana

Configuration
-------------

1. Go to **Settings > General Settings > Asana**.
2. Enter your **Workspace ID** and **App Token** (Personal Access Token from Asana Developer settings).
3. Click the **Test Connection** button to verify that the credentials are valid and connectivity is established.
4. To import existing projects and tasks from Asana, click **Import Projects and Tasks**.
5. To export projects from Odoo to Asana, navigate to **Project > Projects**, switch to list view, select the desired projects, and choose **Export to Asana** from the **Action** menu.

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
Bugs are tracked on GitHub Issues. In case of trouble, please check there if
your issue has already been reported.

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__

Further information
===================
HTML Description: `<static/description/index.html>`__
