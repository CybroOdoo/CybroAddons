TRANSLITERATE WIDGET
====================
Transliterate widget for Odoo client

Credits
=======
Credits for https://www.google.com/jsapi
Developer: Varsha Vivek K @ cybrosys, Contact: odoo@cybrosys.com

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


