MULTIPLE DATE PICKER WIDGET
===========================
Multiple date picker widget for Odoo client

Credits
=======
Credits for https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.7.1/js/bootstrap-datepicker.min.js
Developer: Varsha Vivek K @ cybrosys, Contact: odoo@cybrosys.com

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


