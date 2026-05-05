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
from odoo.tests import common, tagged
from odoo import fields
from dateutil.relativedelta import relativedelta

@tagged('post_install', '-at_install')
class TestWarranty(common.TransactionCase):

    def setUp(self):
        super(TestWarranty, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Customer'})
        self.product = self.env['product.product'].create({
            'name': 'Warranty Product',
            'is_warranty_available': True,
            'warranty_duration': 12,
            'warranty_period_type': 'months',
            'warranty_type': 'full',
            'list_price': 100.0,
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })]
        })

    def test_01_warranty_generation_on_confirm(self):
        """ Test that is_warranty_check is set on sale order confirm"""
        self.sale_order.action_confirm()
        self.assertTrue(self.sale_order.is_warranty_check, "Warranty check should be true")

    def test_02_manual_warranty_registration(self):
        """ Test manual generation of warranty registration via smart tab action"""
        self.sale_order.action_confirm()
        self.sale_order.action_open_smart_tab()
        
        registration = self.env['warranty.registration'].search([
            ('sale_order_id', '=', self.sale_order.id),
            ('product_id', '=', self.product.id)
        ])
        self.assertTrue(registration, "Warranty registration should be created")
        self.assertEqual(registration.warranty_type, 'full')
        
        # Check expiry date (12 months)
        expected_expiry = fields.Date.context_today(self.sale_order) + relativedelta(months=12)
        self.assertEqual(registration.expiry_date, expected_expiry)

    def test_03_flexible_periods(self):
        """ Test different warranty periods (Days, Years)"""
        product_days = self.env['product.product'].create({
            'name': 'Days Product',
            'is_warranty_available': True,
            'warranty_duration': 30,
            'warranty_period_type': 'days',
        })
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product_days.id,
                'product_uom_qty': 1,
            })]
        })
        so.action_confirm()
        so.action_open_smart_tab()
        
        reg = self.env['warranty.registration'].search([('sale_order_id', '=', so.id)])
        expected_expiry = fields.Date.context_today(so) + relativedelta(days=30)
        self.assertEqual(reg.expiry_date, expected_expiry)

    def test_04_automatic_generation_on_delivery(self):
        """ Test that warranty is generated when delivery is validated """
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids[0]
        # Set quantities
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        
        picking.button_validate()
        
        registration = self.env['warranty.registration'].search([
            ('sale_order_id', '=', self.sale_order.id),
            ('product_id', '=', self.product.id)
        ])
        self.assertTrue(registration, "Warranty registration should be automatically created on delivery")
