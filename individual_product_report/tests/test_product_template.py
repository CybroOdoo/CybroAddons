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


class TestProductTemplate(TransactionCase):
    """Tests for the Sales Report smart-button action on product.template."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------
    def setUp(self):
        super().setUp()
        self.Template = self.env['product.template']
        self.template = self.Template.create({
            'name': 'Test Product Template',
            'list_price': 200.0,
        })

    # ------------------------------------------------------------------
    # Return value structure
    # ------------------------------------------------------------------
    def test_action_returns_dict(self):
        """Method must return a dict (the act_window action)."""
        action = self.template.action_view_sales_report()
        self.assertIsInstance(action, dict)

    def test_action_res_model_is_sale_report(self):
        """The returned action must target sale.report."""
        action = self.template.action_view_sales_report()
        self.assertEqual(action.get('res_model'), 'sale.report')

    def test_action_view_mode_is_graph(self):
        """The returned action's view_mode must be 'graph'."""
        action = self.template.action_view_sales_report()
        self.assertEqual(action.get('view_mode'), 'graph')

    def test_action_name_is_sales_analysis(self):
        """The action name should be 'Sales Analysis'."""
        action = self.template.action_view_sales_report()
        self.assertEqual(action.get('name'), 'Sales Analysis')

    # ------------------------------------------------------------------
    # Domain
    # ------------------------------------------------------------------
    def test_action_domain_filters_by_product_tmpl_id(self):
        """Domain must filter sale.report by product_tmpl_id in self.ids."""
        action = self.template.action_view_sales_report()
        self.assertIn(
            ('product_tmpl_id', 'in', self.template.ids),
            action.get('domain', [])
        )

    def test_action_domain_for_multiple_templates(self):
        """Domain must include all ids when called on a multi-record recordset."""
        template_2 = self.Template.create({'name': 'Second Template', 'list_price': 150.0})
        templates = self.template + template_2
        action = templates.action_view_sales_report()
        domain = action.get('domain', [])
        self.assertIn(('product_tmpl_id', 'in', templates.ids), domain)
        self.assertIn(self.template.id, templates.ids)
        self.assertIn(template_2.id, templates.ids)

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------
    def test_action_context_graph_measure(self):
        """Context must set graph_measure to ['product_uom_qty']."""
        action = self.template.action_view_sales_report()
        context = action.get('context', {})
        self.assertEqual(context.get('graph_measure'), ['product_uom_qty'])

    def test_action_context_active_model(self):
        """Context active_model must be 'sale.report'."""
        action = self.template.action_view_sales_report()
        context = action.get('context', {})
        self.assertEqual(context.get('active_model'), 'sale.report')

    def test_action_context_search_default_sales(self):
        """Context must set search_default_Sales to 1."""
        action = self.template.action_view_sales_report()
        context = action.get('context', {})
        self.assertEqual(context.get('search_default_Sales'), 1)

    def test_action_context_time_ranges(self):
        """Context time_ranges must filter on 'date' field for the last 365 days."""
        action = self.template.action_view_sales_report()
        context = action.get('context', {})
        time_ranges = context.get('time_ranges', {})
        self.assertEqual(time_ranges.get('field'), 'date')
        self.assertEqual(time_ranges.get('range'), 'last_365_days')

    def test_action_context_groupby_date(self):# -*- coding: utf-8 -*-
        """Context must group results by 'date'."""
        action = self.template.action_view_sales_report()
        context = action.get('context', {})
        self.assertEqual(context.get('groupby'), 'date')

    def test_action_context_active_id_from_environment(self):
        """Context active_id must reflect env.context active_id when provided."""
        template_with_ctx = self.template.with_context(active_id=self.template.id)
        action = template_with_ctx.action_view_sales_report()
        context = action.get('context', {})
        self.assertEqual(context.get('active_id'), self.template.id)

    def test_action_context_active_id_none_when_absent(self):
        """Context active_id should be None if not present in env.context."""
        action = self.template.action_view_sales_report()
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

    # ------------------------------------------------------------------
    # Cross-model consistency with product.product
    # ------------------------------------------------------------------
    def test_template_and_variant_use_same_underlying_action(self):
        """Both product.template and product.product actions must reference
        the same underlying ir.actions.act_window record."""
        template_action = self.template.action_view_sales_report()
        variant = self.template.product_variant_ids[:1]
        variant_action = variant.action_view_sales_report()
        self.assertEqual(template_action.get('res_model'), variant_action.get('res_model'))
        self.assertEqual(template_action.get('view_mode'), variant_action.get('view_mode'))
        self.assertEqual(template_action.get('name'), variant_action.get('name'))
