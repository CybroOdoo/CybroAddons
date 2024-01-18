.. image:: https://img.shields.io/badge/license-AGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

Transliterate Widget
====================
Transliterate widget for Odoo client

Configuration
=============
- Additional Configuration not required

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
General Public License, Version 3 (AGPL v3).
(https://www.gnu.org/licenses/agpl-3.0-standalone.html)

Credits
=======
- Credits for https://www.google.com/jsapi
- Developer:
            (V17)  Mufeeda Shirin,
            (V16)  Pranav T V,
            (V15)  Pranav T V,
            (V14)  Pranav T V,
            (V13) Varsha Vivek K ,
- Contact: odoo@cybrosys.com

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Usage
=====
You need to declare a char field.

    transliterate = fields.Char(string="Transliterate")

In the view declaration,
    ...
    <field name="arch" type="xml">
        <form string="View name">
            ...
            <field name="transliterate" widget="transliterate"/>
            ...
        </form>
    </field>
    ...

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
