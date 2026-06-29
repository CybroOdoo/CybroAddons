# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from datetime import date, timedelta
from odoo.tests import TransactionCase, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestSaleRecurring(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleRecurring, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner'
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
            'is_storable': True,
        })
        
        cls.recurring = cls.env['sale.recurring'].create({
            'title': 'Test Recurring',
            'partner_id': cls.partner.id,
            'start_date': fields.Date.today(),
            'stop_after': 10,
            'order_line_ids': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_uom_qty': 2.0,
                    'price_unit': 100.0,
                })
            ]
        })

    def test_01_create(self):
        """Test if the recurring sequence is properly generated."""
        self.assertNotEqual(self.recurring.name, 'New', 'The name should have been assigned a sequence.')
        self.assertTrue(self.recurring.name)

    def test_02_onchange_start_date(self):
        """Test if _onchange_start_date calculates end_date correctly."""
        self.recurring._onchange_start_date()
        expected_end_date = self.recurring.start_date + timedelta(days=self.recurring.stop_after)
        self.assertEqual(self.recurring.end_date, expected_end_date, 'End date should be properly updated based on stop_after')

    def test_03_action_create_sale_order(self):
        """Test action_create_sale_order to create sale order from recurring."""
        self.recurring.action_create_sale_order()
        sale_order = self.env['sale.order'].search([('recurring_order_id', '=', self.recurring.id)])
        self.assertTrue(sale_order, 'Sale order should be created from recurring.')
        self.assertEqual(sale_order.partner_id, self.partner)
        self.assertEqual(len(sale_order.order_line), 1)

    def test_04_action_cancel_recurring_order(self):
        """Test setting state to cancelled."""
        self.recurring.action_cancel_recurring_order()
        self.assertEqual(self.recurring.state, 'cancelled')

    def test_05_action_renew(self):
        """Test action_renew setting state back to running."""
        self.recurring.action_cancel_recurring_order()
        self.recurring.action_renew()
        self.assertEqual(self.recurring.state, 'running')

    def test_06_compute_total_sale_quotation_and_order(self):
        """Test compute methods for quotations and orders."""
        self.recurring.action_create_sale_order()
        
        # Check Quotations count
        self.recurring._compute_total_sale_quotation()
        self.assertEqual(self.recurring.total_sale_quotation, 1)

        # Confirm the Sale Order
        sale_order = self.env['sale.order'].search([('recurring_order_id', '=', self.recurring.id)])
        sale_order.action_confirm()

        # Check Sales Order count
        self.recurring._compute_total_sale_order()
        self.assertEqual(self.recurring.total_sale_order, 1)

    def test_07_action_get_sale_orders(self):
        """Test action_get_sale_orders returning the correct action dict."""
        action = self.recurring.action_get_sale_orders()
        self.assertEqual(action['res_model'], 'sale.order')
        self.assertIn(('recurring_order_id', '=', self.recurring.id), action['domain'])
        self.assertIn(('state', '=', 'sale'), action['domain'])

    def test_08_action_get_sale_quotations(self):
        """Test action_get_sale_quotations returning the correct action dict."""
        action = self.recurring.action_get_sale_quotations()
        self.assertEqual(action['res_model'], 'sale.order')
        self.assertIn(('recurring_order_id', '=', self.recurring.id), action['domain'])
        self.assertIn(('state', 'in', ['draft', 'sent']), action['domain'])

    def test_09_action_archive_unarchive(self):
        """Test archive and unarchive toggle."""
        self.recurring.action_archive_orders()
        self.assertFalse(self.recurring.active)
        self.recurring.action_unarchive_orders()
        self.assertTrue(self.recurring.active)

    def test_10_cron_sale_order_creation(self):
        """Test cron_sale_order_creation method logic."""
        # Manually ensure state and dates are set for cron test
        self.recurring.state = 'running'
        self.recurring._onchange_start_date()
        
        # Call the cron function
        self.recurring.cron_sale_order_creation()
        
        sale_orders = self.env['sale.order'].search([('recurring_order_id', '=', self.recurring.id)])
        # Based on cron logic, today is between start and end date, so it creates an order
        self.assertTrue(sale_orders)
        
        # Test expired logic
        self.recurring.end_date = fields.Date.today() - timedelta(days=5)
        self.recurring.cron_sale_order_creation()
        self.assertEqual(self.recurring.state, 'expired')
