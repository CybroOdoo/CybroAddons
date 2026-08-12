# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#############################################################################
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestProductDynamicField(TransactionCase):
    """Test ProductDynamicField wizard from wizard/product_dynamic_field.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard_model = cls.env['product.dynamic.fields']
        cls.product_model = cls.env['ir.model'].search([('model', '=', 'product.template')], limit=1)
        cls.attachment_model = cls.env['ir.model'].search([('model', '=', 'ir.attachment')], limit=1)
        
        cls.position_field = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.product_model.id),
            ('name', '=', 'name'),
            ('state', '=', 'base')
        ], limit=1)

    def test_get_possible_field_types(self):
        """Test that get_possible_field_types excludes certain field types."""
        types = self.wizard_model.get_possible_field_types()
        type_keys = [t[0] for t in types]
        
        self.assertNotIn('one2many', type_keys)
        self.assertNotIn('reference', type_keys)
        self.assertNotIn('properties', type_keys)
        self.assertNotIn('properties_definition', type_keys)
        
        self.assertIn('char', type_keys)
        self.assertIn('integer', type_keys)

    def test_set_domain(self):
        """Test set_domain returns correct domain for position fields."""
        wizard = self.wizard_model.create({
            'name': 'x_test_field',
            'field_type': 'char',
            'position': 'after',
            'position_field': self.position_field.id,
            'model_id': self.product_model.id,
        })
        
        domain = wizard.set_domain()
        
        self.assertIsInstance(domain, list)
        self.assertEqual(domain[0], ('model_id', '=', self.product_model.id))
        self.assertEqual(domain[1], ('state', '=', 'base'))
        self.assertEqual(domain[2][0], 'name')
        self.assertEqual(domain[2][1], 'in')

    def test_set_default(self):
        """Test _set_default returns domain locking to product.template."""
        wizard = self.wizard_model.create({
            'name': 'x_test_field',
            'field_type': 'char',
            'position': 'after',
            'position_field': self.position_field.id,
            'model_id': self.product_model.id,
        })
        
        domain = wizard._set_default()
        self.assertEqual(domain, [('id', '=', self.product_model.id)])

    def test_create_fields(self):
        """Test create_fields correctly creates an ir.model.fields and ir.ui.view."""
        existing_field = self.env['ir.model.fields'].search([('name', '=', 'x_test_dynamic_char'), ('model_id', '=', self.product_model.id)])
        if existing_field:
            existing_field.unlink()
            
        existing_view = self.env['ir.ui.view'].search([('name', '=', 'product.dynamic.fields')])
        if existing_view:
            existing_view.unlink()

        wizard = self.wizard_model.create({
            'name': 'x_test_dynamic_char',
            'field_description': 'Test Dynamic Char',
            'field_type': 'char',
            'position_field': self.position_field.id,
            'position': 'after',
            'model_id': self.product_model.id,
        })
        
        result = wizard.create_fields()
        self.assertEqual(result.get('tag'), 'reload')
        created_field = self.env['ir.model.fields'].search([
            ('name', '=', 'x_test_dynamic_char'),
            ('model_id', '=', self.product_model.id)
        ])
        self.assertTrue(created_field)
        self.assertTrue(created_field.is_dynamic)
        self.assertEqual(created_field.ttype, 'char')
        created_view = self.env['ir.ui.view'].search([
            ('name', '=', 'product.dynamic.fields'),
            ('model', '=', 'product.template')
        ], limit=1)
        self.assertTrue(created_view)
        self.assertIn('<field name="x_test_dynamic_char"/>', created_view.arch_base)

    def test_onchange_widget(self):
        """Test that widget many2many_binary sets ref_model_id to ir.attachment."""
        widget = self.env['field.widget'].create({
            'name': 'many2many_binary',
            'description': 'Many2many Binary',
            'data_type': 'many2many'
        })
        wizard = self.wizard_model.create({
            'name': 'x_test_m2m',
            'field_type': 'many2many',
            'position_field': self.position_field.id,
            'position': 'after',
            'widget': widget.id,
            'model_id': self.product_model.id,
        })
        
        wizard._onchange_widget()
        self.assertEqual(wizard.ref_model_id.id, self.env.ref('base.model_ir_attachment').id)

    def test_onchange_ref_model_id_error(self):
        """Test UserError raised if ref_model_id is not ir.attachment for many2many_binary."""
        widget = self.env['field.widget'].create({
            'name': 'many2many_binary',
            'description': 'Many2many Binary',
            'data_type': 'many2many'
        })
        
        wrong_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        
        wizard = self.wizard_model.create({
            'name': 'x_test_m2m_error',
            'field_type': 'many2many',
            'position_field': self.position_field.id,
            'position': 'after',
            'widget': widget.id,
            'ref_model_id': wrong_model.id,
            'model_id': self.product_model.id,
        })
        
        with self.assertRaises(UserError) as cm:
            wizard._onchange_ref_model_id()
        self.assertIn('This widget is only available for model Attachment', str(cm.exception))
