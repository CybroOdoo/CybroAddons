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
from odoo.exceptions import UserError
from datetime import date, timedelta

class TestSaleOrderDashboard(TransactionCase):
    """Test cases for the Sale Order model extended for the dashboard."""

    def setUp(self):
        """Set up the test data for the dashboard test cases."""
        super(TestSaleOrderDashboard, self).setUp()
        self.partner = self.env['res.partner'].search([], limit=1)
        if not self.partner:
            self.partner = self.env['res.partner'].create({'name': 'Test Dashboard Partner'})

        self.product = self.env['product.product'].search([], limit=1)
        if not self.product:
            self.product_category = self.env['product.category'].search([], limit=1)
            if not self.product_category:
                self.product_category = self.env['product.category'].create({'name': 'Test Category'})
            self.product = self.env['product.product'].create({
                'name': 'Test Dashboard Product',
                'list_price': 100.0,
                'categ_id': self.product_category.id,
            })
        else:
            self.product_category = self.product.categ_id
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })]
        })
        self.sale_order.action_confirm()
        
        self.today = date.today()

    def test_01_get_range(self):
        """Test the _get_range method with various filter keys."""
        # This week
        start, end = self.env['sale.order']._get_range('this_week')
        expected_start = self.today - timedelta(days=self.today.weekday())
        expected_end = min(expected_start + timedelta(days=6), self.today)
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)

        # This month
        start, end = self.env['sale.order']._get_range('this_month')
        self.assertEqual(start, self.today.replace(day=1))
        self.assertEqual(end, self.today)

        # This year
        start, end = self.env['sale.order']._get_range('this_year')
        self.assertEqual(start, self.today.replace(month=1, day=1))
        self.assertEqual(end, self.today)

        # Custom range
        custom_start = self.today - timedelta(days=10)
        custom_end = self.today - timedelta(days=5)
        start, end = self.env['sale.order']._get_range('custom', custom_start, custom_end)
        self.assertEqual(start, custom_start)
        self.assertEqual(end, custom_end)

        # Custom range invalid
        with self.assertRaises(UserError):
            self.env['sale.order']._get_range('custom', custom_end, custom_start)

        # Invalid filter
        start, end = self.env['sale.order']._get_range('invalid')
        self.assertEqual(start, None)
        self.assertEqual(end, None)

    def test_02_build_global_domain(self):
        """Test _build_global_domain method."""
        base_domain = [('state', '=', 'sale')]
        
        # Default (this_week)
        filters = {}
        domain = self.env['sale.order']._build_global_domain(base_domain, filters)
        self.assertTrue(any(d[0] == 'date_order' and d[1] == '>=' for d in domain if isinstance(d, tuple)))
        
        # Custom
        custom_start = self.today - timedelta(days=10)
        custom_end = self.today - timedelta(days=5)
        filters = {
            'global_filter': 'custom',
            'custom_range': {
                'from': custom_start,
                'to': custom_end
            }
        }
        domain = self.env['sale.order']._build_global_domain(base_domain, filters)
        self.assertIn(('date_order', '>=', custom_start), domain)
        self.assertIn(('date_order', '<=', custom_end), domain)
        
    def test_03_get_tile_domain(self):
        """Test get_tile_domain method."""
        base_domain = [('state', '=', 'sale')]
        filters = {'global_filter': 'this_month'}
        domain = self.env['sale.order'].get_tile_domain(base_domain, filters)
        self.assertTrue(any(d[0] == 'date_order' and d[1] == '>=' for d in domain if isinstance(d, tuple)))

    def test_04_get_sales_dashboard_data(self):
        """Test get_sales_dashboard_data method."""
        # With default filters
        filters = {}
        data = self.env['sale.order'].get_sales_dashboard_data(filters)
        
        self.assertIn('sales_by_team', data)
        self.assertIn('sales_by_person', data)
        self.assertIn('top_customers', data)
        self.assertIn('top_products', data)
        self.assertIn('lowest_products', data)
        self.assertIn('overdue_customers', data)
        self.assertIn('order_status', data)
        self.assertIn('invoice_status', data)
        self.assertIn('product_categories', data)
        self.assertIn('sales_info', data)
        self.assertIn('new_vs_returning', data)
        
        # Check sales_info values
        self.assertGreaterEqual(data['sales_info']['sale_orders'], 1)
        self.assertIn('conversion_rate', data['sales_info'])
        
        # Test with custom filters
        filters = {
            'global_filter': 'this_year',
            'product_category_id': self.product_category.id,
            'low_product_category_id': self.product_category.id,
        }
        data = self.env['sale.order'].get_sales_dashboard_data(filters)
        self.assertTrue(isinstance(data, dict))
