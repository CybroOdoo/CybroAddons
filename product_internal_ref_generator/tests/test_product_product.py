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


class TestProductProduct(TransactionCase):
    """ Test for Product Product Internal Reference Generator """

    @classmethod
    def setUpClass(cls):
        super(TestProductProduct, cls).setUpClass()
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
        
        # Reset sequences to ensure deterministic output
        cls.env.ref('product_internal_ref_generator.product_sequence_ref').write({'number_next': 1})
        
        cls.category = cls.env['product.category'].create({
            'name': 'All',
        })

    def test_01_product_product_auto_generate(self):
        """ Test automatic generation of internal reference on product variant """
        product = self.env['product.product'].create({
            'name': 'TestService',
            'type': 'service',
            'categ_id': self.category.id,
        })
        # Format: Service:Tes-All_00001
        self.assertTrue(product.default_code)
        self.assertIn('Service:', product.default_code)
        self.assertIn('Tes-', product.default_code)
        self.assertIn('All_', product.default_code)

    def test_02_action_generate_internal_ref_pro(self):
        """ Test manual generation of internal reference for variant from action """
        # Disable auto-generate to create without default_code
        self.env['ir.config_parameter'].sudo().set_param(
            'product_internal_ref_generator.auto_generate_internal_ref', False)
        
        product = self.env['product.product'].create({
            'name': 'ManualProduct',
            'type': 'consu',
            'categ_id': self.category.id,
        })
        self.assertFalse(product.default_code)
        
        product.with_context(active_ids=[product.id]).action_generate_internal_ref_pro()
        self.assertTrue(product.default_code)
        self.assertIn('Goods:', product.default_code)
        self.assertIn('Man-', product.default_code)
