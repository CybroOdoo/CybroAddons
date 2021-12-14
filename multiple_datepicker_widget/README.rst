MULTIPLE DATE PICKER WIDGET
===========================
Multiple date picker widget for Odoo Odoo 14.

Credits
-------
* Cybrosys Techno Solutions <https://cybrosys.com/>
* Credits for https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.7.1/js/bootstrap-datepicker.min.js

Usage
=====
You need to declare a char field.

    multi_dates = fields.Char(string="Multiple Dates")

In the view declaration,
    ...
    <field name="arch" type="xml">
        <form string="View name">
            ...
            <field name="multi_dates" widget="multiple_datepicker"/>
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
https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html

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