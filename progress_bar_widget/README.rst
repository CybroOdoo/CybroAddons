PROGRESS BAR WIDGET
====================
New Progress Bar Widget for Odoo 15.

Credits
-------
* Cybrosys Techno Solutions <https://cybrosys.com/>

Usage
=====
You need to declare a float field.
    progress = fields.Float(string='Progress', default=0.0)

In the view declaration,
    ...
    <field name="arch" type="xml">
        <form string="View name">
            ...
            <field name="progress" widget="progress_bar_widget"/>
            ...
        </form>
    </field>
    ...

Installation
============
    - https://www.odoo.com/documentation/15.0/setup/install.html
    - Install our custom addon

License
-------
General Public License, Version 3 (LGPL v3).
https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html

Company
-------
* Cybrosys Techno Solutions <https://cybrosys.com/>

Contacts
--------
* Mail Contact : odoo@cybrosys.com

Bug Tracker
-----------
Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Maintainer
==========
This module is maintained by Cybrosys Technologies.

For support and more information, please visit https://www.cybrosys.com

Further information
===================
HTML Description: `<static/description/index.html>`__