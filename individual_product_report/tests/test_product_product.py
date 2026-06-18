# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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


class TestProductProduct(TransactionCase):
    """Tests for the Sales Report smart-button action on product.product."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------
    def setUp(self):
        super().setUp()
        self.Product = self.env['product.product']
        self.product = self.Product.create({
            'name': 'Test Product Variant',
            'list_price': 100.0,
        })


    # ------------------------------------------------------------------
    # Return value structure
    # ------------------------------------------------------------------
    def test_action_returns_dict(self):
        """Method must return a dict (the act_window action)."""
        action = self.product.action_view_sales_report()
        self.assertIsInstance(action, dict)

    def test_action_res_model_is_sale_report(self):
        """The returned action must target sale.report."""
        action = self.product.action_view_sales_report()
        self.assertEqual(action.get('res_model'), 'sale.report')

    def test_action_view_mode_is_graph(self):
        """The returned action's view_mode must be 'graph'."""
        action = self.product.action_view_sales_report()
        self.assertEqual(action.get('view_mode'), 'graph')

    def test_action_name_is_sales_analysis(self):
        """The action name should be 'Sales Analysis'."""
        action = self.product.action_view_sales_report()
        self.assertEqual(action.get('name'), 'Sales Analysis')

    # ------------------------------------------------------------------
    # Domain
    # ------------------------------------------------------------------
    def test_action_domain_filters_by_product_id(self):
        """Domain must filter sale.report by product_id in self.ids."""
        action = self.product.action_view_sales_report()
        self.assertIn(('product_id', 'in', self.product.ids), action.get('domain', []))

    def test_action_domain_for_multiple_products(self):
        """Domain must include all ids when called on a multi-record recordset."""
        product_2 = self.Product.create({'name': 'Second Variant', 'list_price': 50.0})
        products = self.product + product_2
        action = products.action_view_sales_report()
        domain = action.get('domain', [])
        self.assertIn(('product_id', 'in', products.ids), domain)
        self.assertIn(self.product.id, products.ids)
        self.assertIn(product_2.id, products.ids)

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------
    def test_action_context_graph_measure(self):
        """Context must set graph_measure to ['product_uom_qty']."""
        action = self.product.action_view_sales_report()
        context = action.get('context', {})
        self.assertEqual(context.get('graph_measure'), ['product_uom_qty'])

    def test_action_context_active_model(self):
        """Context active_model must be 'sale.report'."""
        action = self.product.action_view_sales_report()
        context = action.get('context', {})
        self.assertEqual(context.get('active_model'), 'sale.report')

    def test_action_context_search_default_sales(self):
        """Context must set search_default_Sales to 1."""
        action = self.product.action_view_sales_report()
        context = action.get('context', {})
        self.assertEqual(context.get('search_default_Sales'), 1)

    def test_action_context_time_ranges(self):
        """Context time_ranges must filter on 'date' field for the last 365 days."""
        action = self.product.action_view_sales_report()
        context = action.get('context', {})
        time_ranges = context.get('time_ranges', {})
        self.assertEqual(time_ranges.get('field'), 'date')
        self.assertEqual(time_ranges.get('range'), 'last_365_days')

    def test_action_context_groupby_date(self):
        """Context must group results by 'date'."""
        action = self.product.action_view_sales_report()
        context = action.get('context', {})
        self.assertEqual(context.get('groupby'), 'date')

    def test_action_context_active_id_from_environment(self):
        """Context active_id must reflect env.context active_id when provided."""
        product_with_ctx = self.product.with_context(active_id=self.product.id)
        action = product_with_ctx.action_view_sales_report()
        context = action.get('context', {})
        self.assertEqual(context.get('active_id'), self.product.id)

    def test_action_context_active_id_none_when_absent(self):
        """Context active_id should be None if not present in env.context."""
        action = self.product.action_view_sales_report()
        context = action.get('context', {})
        self.assertIsNone(context.get('active_id'))

    # ------------------------------------------------------------------
    # Underlying XML action reference
    # ------------------------------------------------------------------
    def test_referenced_action_xmlid_exists(self):
        """The XML action 'individual_product_report.report_sales_product_graph'
        referenced by the method must be resolvable."""
        action_rec = self.env.ref(
            'individual_product_report.report_sales_product_graph'
        )
        self.assertTrue(action_rec.exists())
        self.assertEqual(action_rec.res_model, 'sale.report')
        self.assertEqual(action_rec.view_mode, 'graph')
