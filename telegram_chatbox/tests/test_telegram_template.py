# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase

class TestTelegramTemplate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_model = cls.env["ir.model"].search([("model", "=", "sale.order")], limit=1)
        cls.partner = cls.env["res.partner"].create({"name": "David"})
        cls.sale_order = cls.env["sale.order"].create({
            "partner_id": cls.partner.id,
        })

    def test_onchange_message_syncs_variables(self):
        """Test template variables update dynamically based on the placeholders in the message body."""
        template = self.env["telegram.template"].new({
            "name": "Sync Verification",
            "model_id": self.sale_model.id,
            "message": "Hello {{customer_name}}, order {{order_number}} is confirmed.",
        })
        
        # Trigger onchange manually
        template._onchange_message()
        variables = template.dynamic_variable_ids
        self.assertEqual(len(variables), 2)
        self.assertTrue(any(v.name == 'customer_name' for v in variables))
        self.assertTrue(any(v.name == 'order_number' for v in variables))

        # Update message to remove one variable
        template.message = "Hello {{customer_name}} only."
        template._onchange_message()
        variables = template.dynamic_variable_ids
        self.assertEqual(len(variables), 1)
        self.assertEqual(variables[0].name, 'customer_name')

    def test_render_template_with_record(self):
        """Test rendering of template with actual record fields."""
        template = self.env["telegram.template"].create({
            "name": "Sync Verification",
            "model_id": self.sale_model.id,
            "message": "Order {{order_number}} is confirmed.",
        })
        name_field = self.env["ir.model.fields"].search([
            ("model_id", "=", self.sale_model.id),
            ("name", "=", "name")
        ], limit=1)
        
        self.env["telegram.template.variable"].create({
            "template_id": template.id,
            "name": "order_number",
            "model_id": self.sale_model.id,
            "field_id": name_field.id
        })

        rendered = template.render_template(template.message, record=self.sale_order)
        self.assertEqual(rendered, f"Order {self.sale_order.name} is confirmed.")
