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

Sync Google Task With Project Task
==================================

Sync your project tasks with Google Tasks: export tasks and their subtasks
to your default Google Tasks list, keep them updated, and import the tasks
created in Google Tasks into Odoo.

Key Features
------------

* Connect a Google account once from Project > Configuration > Google Task
  Credential, with your own Google Cloud OAuth client
* Export a task and its subtasks with the Export to Google Task button on the
  task form, from the task list, or from the import/export wizard
* Exported tasks are updated in Google Tasks when their name, description,
  deadline or subtasks change; a task deleted in Google Tasks is created again
* Import the Google tasks that are not in Odoo yet, into a project (subtasks
  stay under their parent task) or as your private tasks
* Project > Google Tasks > Tasks lists the exported and imported tasks
* Works with both Community and Enterprise editions

Installation
------------
No external dependencies. The module depends on Project (``project``).

Configuration
-------------
1. In Google Cloud Console, enable the Google Tasks API and create an OAuth
   client of type Web application, with your Odoo URL followed by
   ``/google_task_authentication`` as the authorized redirect URI.
2. In Odoo, open Project > Configuration > Google Task Credential (project
   administrators), enter the Client ID and Client Secret, check the
   redirect URI and click Authenticate.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

Credits
-------
* Developers: (V18) Shikhil, (V19) Athul Raj B S, (V20) Yadhu Shankar

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
