# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    """ Test for Product Template Internal Reference Generator """

    @classmethod
    def setUpClass(cls):
        super(TestProductTemplate, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Configure parameters
        cls.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.auto_generate_internal_ref', True)
        cls.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.product_name_config', True)
        cls.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.pro_name_digit', 3)
        cls.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.pro_name_separator', '-')
        cls.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.pro_categ_config', True)
        cls.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.pro_categ_digit', 3)
        cls.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.pro_categ_separator', '_')
        cls.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.pro_template_config', True)
        cls.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.pro_template_digit', 2)
        cls.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.pro_template_separator', '/')
        
        # Reset sequences to ensure deterministic output
        cls.env.ref('product_internal_ref_generator.attribute_sequence_ref').write({'number_next': 1})
        
        cls.category = cls.env['product.category'].create({
            'name': 'All',
        })
        
        cls.attribute = cls.env['product.attribute'].create({
            'name': 'Color',
            'create_variant': 'no_variant'
        })
        cls.value = cls.env['product.attribute.value'].create({
            'name': 'Red',
            'attribute_id': cls.attribute.id,
        })

    def test_01_product_template_auto_generate(self):
        """ Test automatic generation of internal reference on product template """
        product_template = self.env['product.template'].create({
            'name': 'TestProduct',
            'type': 'consu',
            'categ_id': self.category.id,
            'attribute_line_ids': [(0, 0, {
                'attribute_id': self.attribute.id,
                'value_ids': [(6, 0, [self.value.id])]
            })]
        })
        # Format: Goods:Tes-All_Re/00001 (based on logic)
        self.assertTrue(product_template.default_code)
        self.assertIn('Goods:', product_template.default_code)
        self.assertIn('Tes-', product_template.default_code)
        self.assertIn('All_', product_template.default_code)
        self.assertIn('Re/', product_template.default_code)

    def test_02_action_generate_internal_ref(self):
        """ Test manual generation of internal reference from action """
        # Disable auto-generate to create without default_code
        self.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.auto_generate_internal_ref', False)
        
        product_template = self.env['product.template'].create({
            'name': 'ManualTemplate',
            'type': 'combo',
            'categ_id': self.category.id,
        })
        self.assertFalse(product_template.default_code)
        
        product_template.with_context(active_ids=[product_template.id]).action_generate_internal_ref()
        self.assertTrue(product_template.default_code)
        self.assertIn('Combo:', product_template.default_code)
        self.assertIn('Man-', product_template.default_code)
