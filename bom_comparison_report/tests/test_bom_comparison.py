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
#############################################################################
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestBomComparison(TransactionCase):
    """Test the BoM comparison wizard and report."""

    @classmethod
    def setUpClass(cls):
        """Create a product with two bills of materials."""
        super().setUpClass()
        product = cls.env['product.product']
        cls.component_a = product.create({
            'name': 'Component A', 'standard_price': 10.0, 'lst_price': 15.0})
        cls.component_b = product.create({
            'name': 'Component B', 'standard_price': 20.0, 'lst_price': 30.0})
        cls.product_tmpl = cls.env['product.template'].create(
            {'name': 'Finished Product'})
        # Cost 2 x 10 + 1 x 20 = 40, sales price 2 x 15 + 1 x 30 = 60
        cls.bom_1 = cls._bom(cls.component_a, 2.0, cls.component_b, 1.0)
        # Cost 1 x 10 + 2 x 20 = 50, sales price 1 x 15 + 2 x 30 = 75
        cls.bom_2 = cls._bom(cls.component_a, 1.0, cls.component_b, 2.0)

    @classmethod
    def _bom(cls, first, first_qty, second, second_qty, **values):
        return cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_tmpl.id,
            'bom_line_ids': [
                Command.create({'product_id': first.id,
                                'product_qty': first_qty}),
                Command.create({'product_id': second.id,
                                'product_qty': second_qty}),
            ],
            **values,
        })

    def _wizard(self, **values):
        return self.env['bom.comparison'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'bom_ids': [Command.set((self.bom_1 | self.bom_2).ids)],
            **values,
        })

    def _totals(self, wizard):
        return [(line['bom'], line['unit_price'], line['total'])
                for line in wizard._get_comparison_lines()]

    def test_01_cost_analysis(self):
        """The cost of the components, cheapest bill of materials first."""
        wizard = self._wizard(product_unit=3)
        self.assertEqual(wizard.analysis, 'cost')
        self.assertEqual(self._totals(wizard), [
            (self.bom_1, 40.0, 120.0), (self.bom_2, 50.0, 150.0)])

    def test_02_sales_price_analysis(self):
        """The sales price of the components."""
        wizard = self._wizard(analysis='sale_price', product_unit=2)
        self.assertEqual(self._totals(wizard), [
            (self.bom_1, 60.0, 120.0), (self.bom_2, 75.0, 150.0)])

    def test_03_units_of_measure(self):
        """Quantities are converted to the units of the products, and the
        price is for one product even when the BoM makes several."""
        dozen = self.env.ref('uom.product_uom_dozen')
        bom_3 = self._bom(self.component_a, 1.0, self.component_b, 0.0,
                          product_qty=2.0)
        bom_3.bom_line_ids[0].uom_id = dozen
        wizard = self._wizard(bom_ids=[Command.set((self.bom_1 | bom_3).ids)])
        # 1 dozen x 10 = 120 for 2 products: 60 per product
        self.assertIn((bom_3, 60.0, 60.0), self._totals(wizard))

    def test_04_constraints(self):
        """At least two bills of materials and one product."""
        with self.assertRaises(ValidationError):
            self._wizard(bom_ids=[Command.set(self.bom_1.ids)])
        with self.assertRaises(ValidationError):
            self._wizard(product_unit=0)

    def test_05_prefill_from_list(self):
        """The bills of materials selected in the list prefill the
        wizard."""
        wizard = self.env['bom.comparison'].with_context(
            active_model='mrp.bom',
            active_ids=(self.bom_1 | self.bom_2).ids,
        ).new({})
        self.assertEqual(wizard.product_tmpl_id, self.product_tmpl)
        self.assertEqual(wizard.bom_ids._origin, self.bom_1 | self.bom_2)

    def test_06_report(self):
        """The report renders and highlights the cheapest bill of
        materials."""
        wizard = self._wizard()
        # Skip the document layout configurator of a new database
        action = wizard.with_context(
            discard_logo_check=True).action_comparison_report()
        self.assertEqual(action['report_name'],
                         'bom_comparison_report.bom_compare_report')
        html, _type = self.env['ir.actions.report']._render_qweb_html(
            'bom_comparison_report.bom_compare_report', wizard.ids)
        html = html.decode()
        self.assertIn('Profitable BoM', html)
        self.assertIn(self.bom_1.display_name, html)

    def test_07_manufacturing_user(self):
        """A Manufacturing user, without the Settings access, compares the
        bills of materials and prints the report."""
        user = new_test_user(self.env, login='bom_user',
                             groups='base.group_user,mrp.group_mrp_user')
        env = self.env(user=user)
        boms = env['mrp.bom'].browse((self.bom_1 | self.bom_2).ids)
        wizard = env['bom.comparison'].with_context(
            active_model='mrp.bom', active_ids=boms.ids).create({})
        self.assertEqual(wizard.bom_ids, boms)
        self.assertEqual(self._totals(wizard)[0][1:], (40.0, 40.0))
        html, _type = env['ir.actions.report']._render_qweb_html(
            'bom_comparison_report.bom_compare_report', wizard.ids)
        self.assertIn('o_bom_compare_best', html.decode())
