TRANSLITERATE WIDGET
====================
Transliterate widget for Odoo client

Credits
=======
Credits for https://www.google.com/jsapi
* Developer:  V13 Varsha Vivek K , odoo@cybrosys.com
              V14.0  Pranav T V, odoo@cybrosys.com
              V15.0  Pranav T V, odoo@cybrosys.com
              V16.0  Pranav T V, odoo@cybrosys.com


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


