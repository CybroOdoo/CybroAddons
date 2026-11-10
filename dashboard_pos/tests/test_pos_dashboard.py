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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import date
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user
from odoo.tools.misc import format_amount


@tagged('post_install', '-at_install')
class TestPosDashboard(TransactionCase):
    """ Tests of the data provided to the POS dashboard """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(
            cls.env, login='pos_dashboard_manager',
            groups='point_of_sale.group_pos_manager')
        cls.cashier = new_test_user(
            cls.env, login='pos_dashboard_cashier',
            groups='point_of_sale.group_pos_user')
        cls.order_model = cls.env['pos.order'].with_user(cls.manager)
        cls.model_class = type(cls.order_model)
        cls.company = cls.manager.company_id
        cls.partner = cls.env['res.partner'].create({'name': 'Dashboard Customer'})

    def _patch(self, method, **kwargs):
        """ Replace a helper of pos.order for the duration of the test. """
        patcher = patch.object(self.model_class, method, **kwargs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def test_access_restricted_to_managers(self):
        """ The public methods are refused to the users who are not POS
        managers, like the menu of the dashboard. """
        orders = self.env['pos.order'].with_user(self.cashier)
        with self.assertRaises(AccessError):
            orders.get_refund_details()
        with self.assertRaises(AccessError):
            orders.get_details()
        with self.assertRaises(AccessError):
            orders.get_department('pos_hourly_sales')
        with self.assertRaises(AccessError):
            orders.get_the_top_customer()
        with self.assertRaises(AccessError):
            orders.get_the_top_products()
        with self.assertRaises(AccessError):
            orders.get_the_top_categories()

    def test_sales_queries_run(self):
        """ The three sales groupings run on the database. """
        for option in ('pos_hourly_sales', 'pos_daily_sales', 'pos_monthly_sales'):
            result = self.order_model.get_department(option)
            self.assertEqual(len(result), 3)
            self.assertEqual(len(result[0]), len(result[1]))

    def test_sales_queries_with_timezone(self):
        """ The sales use the timezone of the user. """
        self.manager.tz = 'Asia/Kolkata'
        result = self.order_model.get_department('pos_hourly_sales')
        self.assertEqual(result[2], 'Hours')

    def test_hourly_sales(self):
        self._patch('_dashboard_group', return_value=[(9, 120), (10, 80.5)])
        self.assertEqual(
            self.order_model.get_department('pos_hourly_sales'),
            [[120.0, 80.5], ['9', '10'], 'Hours'])

    def test_daily_sales(self):
        self._patch('_dashboard_group', return_value=[(date(2026, 10, 1), 50)])
        self.assertEqual(
            self.order_model.get_department('pos_daily_sales'),
            [[50.0], ['2026-10-01'], 'Days'])

    def test_monthly_sales(self):
        self._patch('_dashboard_group', return_value=[(1, 5), (3, 7)])
        self.assertEqual(
            self.order_model.get_department('pos_monthly_sales'),
            [[5.0, 7.0], ['JAN', 'MAR'], 'Months'])

    def test_counted_states(self):
        """ Only the paid orders of the company are grouped. """
        mocked = self._patch('_dashboard_group', return_value=[])
        self.order_model.get_the_top_customer()
        domain = mocked.call_args.args[0]
        self.assertIn(('state', 'in', ('paid', 'done', 'invoiced')), domain)
        self.assertIn(('company_id', '=', self.company.id), domain)

    def test_details_run(self):
        """ The payment, salesperson and session details run. """
        result = self.order_model.get_details()
        self.assertEqual(
            set(result), {'payment_details', 'salesperson', 'sessions'})
        for session in result['sessions']:
            self.assertIn('session', session)
            self.assertIn('status', session)

    def test_details_with_rows(self):
        method = self.env['pos.payment.method'].new({'name': 'Dashboard Method'})
        self._patch('_dashboard_group', side_effect=[
            [(method, 50.0)],
            [(self.manager, 100.0, 2)],
        ])
        result = self.order_model.get_details()
        currency = self.company.currency_id
        self.assertEqual(
            result['payment_details'],
            [('Dashboard Method', format_amount(self.env, 50.0, currency))])
        self.assertEqual(
            result['salesperson'],
            [(self.manager.name, format_amount(self.env, 100.0, currency), 2)])

    def test_session_status(self):
        """ A configuration without open session is closed. """
        config = self.env['pos.config'].search(
            [('company_id', '=', self.company.id)], limit=1)
        if not config:
            self.skipTest("No point of sale configuration available.")
        result = self.order_model.get_details()
        self.assertIn(config.name, [rec['session'] for rec in result['sessions']])

    def test_refund_details(self):
        result = self.order_model.get_refund_details()
        self.assertEqual(
            set(result),
            {'total_sale', 'total_order_count', 'total_refund_count',
             'total_session', 'today_refund_total', 'today_sale',
             'order_domain', 'refund_domain', 'today_domain',
             'session_domain'})
        self.assertGreaterEqual(result['total_order_count'],
                                result['total_refund_count'])
        self.assertGreaterEqual(result['total_order_count'],
                                result['today_sale'])

    def test_tile_domains_match_counts(self):
        """ The domains sent to the tiles select the counted records. """
        result = self.order_model.get_refund_details()
        orders = self.order_model
        self.assertEqual(
            orders.search_count(result['order_domain']),
            result['total_order_count'])
        self.assertEqual(
            orders.search_count(
                result['order_domain'] + result['refund_domain']),
            result['total_refund_count'])
        self.assertEqual(
            orders.search_count(
                result['order_domain'] + result['today_domain']),
            result['today_sale'])
        self.assertEqual(
            self.env['pos.session'].with_user(self.manager).search_count(
                result['session_domain']),
            result['total_session'])

    def test_today_range(self):
        self.manager.tz = 'Asia/Kolkata'
        start, end = self.order_model._dashboard_today_range()
        self.assertEqual((end - start).total_seconds(), 24 * 3600)

    def test_humanize(self):
        humanize = self.order_model._dashboard_humanize
        self.assertEqual(humanize(0), '0.00')
        self.assertEqual(humanize(999), '999.00')
        self.assertEqual(humanize(1250), '1.25K')
        self.assertEqual(humanize(-2500000), '-2.50M')
        self.assertEqual(humanize(1e30), '1000000000000000.00P')

    def test_top_customer(self):
        self.assertEqual(len(self.order_model.get_the_top_customer()), 2)
        self._patch('_dashboard_group', return_value=[(self.partner, 30)])
        self.assertEqual(
            self.order_model.get_the_top_customer(),
            [[30.0], ['Dashboard Customer']])

    def test_top_products(self):
        self.assertEqual(len(self.order_model.get_the_top_products()), 2)
        template = self.env['product.template'].create({'name': 'Dashboard Product'})
        self._patch(
            '_dashboard_group',
            return_value=[(template.product_variant_id, 4)])
        self.assertEqual(
            self.order_model.get_the_top_products(),
            [[4.0], ['Dashboard Product']])

    def test_top_categories(self):
        self.assertEqual(len(self.order_model.get_the_top_categories()), 2)
        category = self.env['product.category'].create({'name': 'Dashboard Category'})
        template = self.env['product.template'].create({
            'name': 'Dashboard Product',
            'categ_id': category.id,
        })
        self._patch(
            '_dashboard_group',
            return_value=[(template.product_variant_id, 9)])
        self.assertEqual(
            self.order_model.get_the_top_categories(),
            [[9.0], ['Dashboard Category']])
