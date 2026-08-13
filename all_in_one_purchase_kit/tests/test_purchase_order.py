# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestPurchaseOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'PO Test Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'PO Test Product',
            'type': 'consu',
        })

    def test_purchase_order_computes_and_confirm_merging(self):
        """Test merge duplicate lines on button_confirm."""
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 2.0,
                    'price_unit': 50.0,
                    'taxes_id': [(5, 0, 0)],
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 3.0,
                    'price_unit': 50.0,
                    'taxes_id': [(5, 0, 0)],
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 1.0,
                    'price_unit': 60.0,
                    'taxes_id': [(5, 0, 0)],
                })
            ]
        })
        po._compute_number_to_words()
        self.assertIn('Three Hundred', po.number_to_words)
        
        self.assertEqual(len(po.order_line), 3)
        po.button_confirm()
        self.assertEqual(len(po.order_line), 2)
        
        merged_line = po.order_line.filtered(lambda l: l.price_unit == 50.0)
        other_line = po.order_line.filtered(lambda l: l.price_unit == 60.0)
        self.assertEqual(len(merged_line), 1)
        self.assertEqual(merged_line.product_qty, 5.0)
        self.assertEqual(other_line.product_qty, 1.0)

    def test_purchase_order_dashboard_methods(self):
        """Test dashboard query data methods."""
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 10,
                'price_unit': 100.0,
            })]
        })
        po.button_confirm()
        if po.state != 'purchase':
            po.write({'state': 'purchase'})
        
        data = self.env['purchase.order'].get_purchase_data()
        self.assertIn('purchase_orders', data)
        self.assertIn('purchase_amount', data)
        
        mode_data = self.env['purchase.order'].get_select_mode_data('this_year')
        self.assertNotEqual(mode_data, False)
        
        chart_data = self.env['purchase.order'].get_top_chart_data('top_product')
        self.assertTrue(isinstance(chart_data, list))
        
        months_data = self.env['purchase.order'].get_orders_by_month()
        self.assertIn('count', months_data)
        self.assertIn('dates', months_data)
        
        vendors = self.env['purchase.order'].purchase_vendors()
        self.assertTrue(isinstance(vendors, list))
        
        vendor_details = self.env['purchase.order'].purchase_vendor_details(self.partner.id)
        self.assertIn('po_count', vendor_details)
        
        pending_data = self.env['purchase.order'].get_pending_purchase_data()
        self.assertIn('order', pending_data)
        
        upcoming_data = self.env['purchase.order'].get_upcoming_purchase_data()
        self.assertIn('order', upcoming_data)
        
        total_spend = self.env['purchase.order'].total_amount_spend()
        self.assertIn('amount_total', total_spend)

    def test_recommendation_wizard_action(self):
        """Test wizard action is returned correctly."""
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 1.0,
                'price_unit': 100.0,
            })]
        })
        action = po.recommendation_wizard()
        self.assertEqual(action['res_model'], 'product.recommendation')
