.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community%20%7C%20Enterprise-1ABC9C.svg
    :alt: Community and Enterprise Edition

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |maintainer|

Project Report XLS & PDF
========================

Print the tasks of a project as a PDF report or export them to an XLSX
spreadsheet, filtered by task stage and assignee.

Key Features
------------

* A **Print** button on the project form opens the report wizard
* Filter the tasks by assignee and by stage
* PDF report with the project manager, the start and end dates and the task list
* XLSX spreadsheet with the company details, the project details and the task list

Installation
------------
The Python package ``xlsxwriter`` is required for the XLS export::

    pip install xlsxwriter

Configuration
-------------
No additional configuration is required. Every internal user who can read a
project can print its report.

Usage
-----
1. Go to **Project** and open a project.
2. Click **Print** in the header of the project form.
3. Optionally select users in **Assigned to** and stages in **Stage**. Leave a
   filter empty to include all tasks.
4. Click **Print PDF** for the PDF report or **Print XLS** for the XLSX
   spreadsheet.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------
* Cybrosys Techno Solutions <https://www.cybrosys.com>

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Bug Tracker
-----------
For bug reports and support, please contact odoo@cybrosys.com.

Maintainer
----------
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com


This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__

Further information
-------------------
HTML Description: `<static/description/index.html>`__
