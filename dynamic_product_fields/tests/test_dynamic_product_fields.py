# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestDynamicProductFields(TransactionCase):
    def setUp(self):
        super(TestDynamicProductFields, self).setUp()
        self.ProductTemplate = self.env['product.template']
        self.IrModelFields = self.env['ir.model.fields']
        self.IrModel = self.env['ir.model']
        self.DynamicFieldWizard = self.env['product.dynamic.fields']
        self.product_model = self.IrModel.search([('model', '=', 'product.template')])
        self.name_field = self.IrModelFields.search([
            ('model_id', '=', self.product_model.id),
            ('name', '=', 'name')
        ])

    def test_create_dynamic_char_field(self):
        wizard = self.DynamicFieldWizard.create({
            'name': 'x_test_char_field',
            'field_description': 'Test Char Field',
            'model_id': self.product_model.id,
            'field_type': 'char',
            'position_field': self.name_field.id,
            'position': 'after',
        })
        wizard.create_fields()
        field = self.IrModelFields.search([
            ('name', '=', 'x_test_char_field'),
            ('model_id', '=', self.product_model.id)
        ])
        self.assertTrue(field, "Dynamic field should be created.")
        self.assertTrue(field.is_dynamic, "Field should be marked as dynamic.")
        view = self.env['ir.ui.view'].search([
            ('name', '=', 'product.dynamic.fields'),
            ('model', '=', 'product.template'),
            ('mode', '=', 'extension')
        ], limit=1, order='id desc')
        self.assertTrue(view, "Inherited view should be created.")
        self.assertIn('x_test_char_field', view.arch_base, "The field should be in the view architecture.")

    def test_create_dynamic_selection_field_with_widget(self):
        radio_widget = self.env.ref('dynamic_product_fields.field_widgets_radio_widget')
        wizard = self.DynamicFieldWizard.create({
            'name': 'x_test_selection_field',
            'field_description': 'Test Selection Field',
            'model_id': self.product_model.id,
            'field_type': 'selection',
            'selection_field': "[('val1', 'Value 1'), ('val2', 'Value 2')]",
            'position_field': self.name_field.id,
            'position': 'before',
            'widget': radio_widget.id,
        })
        wizard.create_fields()
        field = self.IrModelFields.search([
            ('name', '=', 'x_test_selection_field'),
            ('model_id', '=', self.product_model.id)
        ])
        self.assertTrue(field, "Dynamic selection field should be created.")
        self.assertEqual(field.selection, "[('val1', 'Value 1'), ('val2', 'Value 2')]", "Selection options should match.")
        view = self.env['ir.ui.view'].search([
            ('name', '=', 'product.dynamic.fields'),
            ('model', '=', 'product.template'),
            ('mode', '=', 'extension')
        ], limit=1, order='id desc')
        self.assertTrue(view, "Inherited view with widget should be created.")
        self.assertIn('x_test_selection_field', view.arch_base, "The field should be in the view architecture.")
        self.assertIn('radio', view.arch_base, "The widget should be in the view architecture.")
