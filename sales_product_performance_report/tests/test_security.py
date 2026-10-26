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
#############################################################################
"""Security regression tests: no superuser reports, no shared results."""
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import PerformanceCommon


@tagged('post_install', '-at_install')
class TestPerformanceSecurity(PerformanceCommon):
    """Ensure the reports cannot leak or lock data."""

    def test_product_report_respects_own_documents_rule(self):
        """A user seeing only his orders gets only his revenue."""
        line = self._product_lines(self.alice)
        self.assertEqual(line.revenue, 20.0)
        self.assertEqual(line.total_order, 1)

    def test_sales_report_respects_own_documents_rule(self):
        """A salesman reporting on a colleague sees zero orders."""
        lines = self._sales_lines(self.alice, self.bob)
        self.assertEqual(lines.user_id, self.bob)
        self.assertEqual(lines.total_sale_order, 0)
        self.assertEqual(lines.estimated_revenue, 0.0)

    def test_company_outside_user_scope_is_ignored(self):
        """A company the user does not belong to cannot be reported."""
        other = self.env['res.company'].create({'name': 'Other Company'})
        wizard = self.env['product.performance'].with_user(self.alice).create({
            'categ_id': self.categ.id,
            'product_ids': [Command.set(self.product.product_tmpl_id.ids)]})
        wizard.sudo().company_ids = other
        self.assertEqual(wizard._get_scope_companies(), self.env.company)
        wizard = self.env['sales.performance'].with_user(self.alice).create({})
        wizard.sudo().company_ids = other
        self.assertEqual(wizard._get_scope_companies(), self.env.company)

    def test_runs_do_not_overwrite_each_other(self):
        """Two users reporting on the same product keep their own results."""
        line_a = self._product_lines(self.alice)
        line_b = self._product_lines(self.admin)
        self.assertEqual(line_a.revenue, 20.0)
        self.assertEqual(line_b.revenue, 50.0)

    def test_lines_are_private_to_their_creator(self):
        """A salesman cannot read the lines of another user."""
        line_a = self._product_lines(self.alice)
        line_b = self._product_lines(self.bob)
        Line = self.env['product.performance.line']
        alice_ids = Line.with_user(self.alice).search([]).ids
        self.assertIn(line_a.id, alice_ids)
        self.assertNotIn(line_b.id, alice_ids)

    def test_no_report_data_on_shared_models(self):
        """No performance fields must ever exist on product or users."""
        forbidden = {
            'res.users': ('overall_performance', 'overall_performance_separate',
                          'estimated_revenue', 'net_revenue'),
            'product.template': ('revenue', 'avg_price', 'total_order'),
        }
        for model, names in forbidden.items():
            for name in names:
                self.assertNotIn(name, self.env[model]._fields)

    def test_lines_are_read_only_for_salesmen(self):
        """Report lines cannot be edited, even by their creator."""
        lines = self._product_lines(self.alice)
        with self.assertRaises(AccessError):
            lines.write({'revenue': 1.0})

    def test_menus_do_not_alter_the_sales_app(self):
        """The report menus sit in the standard reporting menu."""
        root = self.env.ref('sale.sale_menu_root')
        report = self.env.ref('sale.menu_sale_report')
        for xmlid in ('menu_product_performance_view',
                      'menu_sales_performance_view'):
            menu = self.env.ref(f'sales_product_performance_report.{xmlid}')
            self.assertEqual(menu.parent_id, report)
        # The Sales app is activated by sale_management, not by this module.
        self.assertTrue(root.active)
