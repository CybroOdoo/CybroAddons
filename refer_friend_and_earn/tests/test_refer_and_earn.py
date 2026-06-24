# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Syamili K (odoo@cybrosys.com)
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

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReferAndEarn(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestReferAndEarn, cls).setUpClass()
        # Setup test data
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Referrer Partner',
            'referral_code': 'TESTREF',
            'points': 100,
            'sign_up': 2
        })
        
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
        })
        
        # Ensure the discount product exists as expected by the module
        cls.discount_product = cls.env['product.product'].sudo().search([('default_code', '=', 'DISCOUNT001')], limit=1)
        if not cls.discount_product:
            cls.discount_product = cls.env['product.product'].create({
                'name': 'Discount Product',
                'default_code': 'DISCOUNT001',
                'list_price': 0.0,
            })
            
        # Create a discount rule
        cls.discount_rule = cls.env['apply.discounts'].create({
            'starting_points': 50,
            'end_points': 150,
            'discount': 10.0, # 10% discount
        })

    def test_01_config_settings_sign_up_points(self):
        """Test setting and getting the signup points config parameter"""
        self.env['ir.config_parameter'].sudo().set_param('refer_friend_and_earn.sign_up_points', '50')
        points = float(self.env['ir.config_parameter'].sudo().get_param('refer_friend_and_earn.sign_up_points'))
        self.assertEqual(points, 50.0, "The sign_up_points parameter should be correctly retrieved as 50.0")

    def test_02_partner_fields(self):
        """Test that partner fields related to refer and earn are correctly stored and retrieved"""
        self.assertEqual(self.partner.referral_code, 'TESTREF', "Partner referral code should match")
        self.assertEqual(self.partner.points, 100, "Partner should have exactly 100 points")
        self.assertEqual(self.partner.sign_up, 2, "Partner should have exactly 2 signups recorded")

    def test_03_apply_discounts_rule(self):
        """Test that the discount rule matches correctly for given points"""
        test_points = 100
        points_rec = self.env['apply.discounts'].search([
            ('starting_points', '<=', test_points),
            ('end_points', '>=', test_points)
        ], order='create_date desc', limit=1)

        self.assertTrue(points_rec, "A discount rule should be found for 100 points")
        self.assertEqual(points_rec.discount, 10.0, "The matched discount rule should provide a 10% discount")
        
    def test_04_sale_order_points_fields(self):
        """Test if the points and discount applied fields are populated correctly on Sale Order"""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'points_applied': 100,
            'discount_applied': 10.0,
        })
        sale_order.write({'order_line': [(0, 0, {
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'price_unit': 100.0,
        })]})
        
        self.assertEqual(sale_order.points_applied, 100.0, "SO points_applied field should store 100")
        self.assertEqual(sale_order.discount_applied, 10.0, "SO discount_applied field should store 10.0")
