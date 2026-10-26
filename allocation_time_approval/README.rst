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

Allocation Time Approval
========================

This module enables managers to review and approve allocated time on project tasks.

Key Features
------------

* Manager approval workflow for allocated hours on project tasks.
* Dedicated manager approval dashboard under **Timesheets > Allocated Hour Approval**.
* Restricted stage transitions ensuring only Project Managers can move tasks in/out of approval stages.
* Overtime safeguard requiring Project Manager approval when spent hours exceed allocated hours before marking a task as Done.
* Automated synchronization of task stages and assignees' personal task stages upon approval, completion, or cancellation.

Installation
------------
No external dependencies.

Configuration
-------------

Assign user access rights under **Settings > Users & Companies > Users** (Access Rights tab under **SERVICES**):

* **Project**:
  * **User**: Allows users to create tasks and request manager approval for allocated hours.
  * **Administrator**: Grants project managers full access to review, approve, or cancel allocated time requests, manage task stage transitions, and access the **Allocated Hour Approval** dashboard (**Timesheets > Allocated Hour Approval**).

* **Timesheets**:
  * **User**: Allows team members to log timesheets on assigned tasks.

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
