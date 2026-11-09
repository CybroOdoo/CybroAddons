# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(Contact : odoo@cybrosys.com)
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
#############################################################################
from odoo import Command
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBomTotalCost(TransactionCase):
    """Test suite for Bill of Materials total cost and unit cost calculations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_kg = cls.env.ref('uom.product_uom_kgm')
        cls.uom_gram = cls.env.ref('uom.product_uom_gram')

        cls.finished_product = cls.env['product.product'].create({
            'name': 'Dining Table',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
        })

        cls.component_table_top = cls.env['product.product'].create({
            'name': 'Table Top',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'standard_price': 40.0,
        })

        cls.component_table_leg = cls.env['product.product'].create({
            'name': 'Table Leg',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'standard_price': 5.0,
        })

        cls.component_varnish = cls.env['product.product'].create({
            'name': 'Wood Varnish Powder',
            'type': 'consu',
            'uom_id': cls.uom_kg.id,
            'standard_price': 20.0,
        })

    def test_01_single_unit_bom_cost(self):
        """Test BOM cost and unit cost when output quantity is 1."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.finished_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({
                    'product_id': self.component_table_top.id,
                    'product_qty': 1.0,
                    'uom_id': self.uom_unit.id,
                }),
                Command.create({
                    'product_id': self.component_table_leg.id,
                    'product_qty': 4.0,
                    'uom_id': self.uom_unit.id,
                }),
            ],
        })

        self.assertEqual(len(bom.bom_line_ids), 2)
        top_line = bom.bom_line_ids.filtered(
            lambda l: l.product_id == self.component_table_top
        )
        leg_line = bom.bom_line_ids.filtered(
            lambda l: l.product_id == self.component_table_leg
        )

        # Line costs: 1 * 40.0 = 40.0; 4 * 5.0 = 20.0
        self.assertEqual(top_line.cost, 40.0)
        self.assertEqual(leg_line.cost, 20.0)

        # For 1 unit: Total cost = 60.0, Unit cost = 60.0
        self.assertEqual(bom.total_bom_cost, 60.0)
        self.assertEqual(bom.bom_cost, 60.0)

    def test_02_multiple_units_bom_cost(self):
        """Test BOM cost when output quantity is greater than 1 (batch production)."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.finished_product.product_tmpl_id.id,
            'product_qty': 5.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({
                    'product_id': self.component_table_top.id,
                    'product_qty': 5.0,
                    'uom_id': self.uom_unit.id,
                }),
                Command.create({
                    'product_id': self.component_table_leg.id,
                    'product_qty': 20.0,
                    'uom_id': self.uom_unit.id,
                }),
            ],
        })

        top_line = bom.bom_line_ids.filtered(
            lambda l: l.product_id == self.component_table_top
        )
        leg_line = bom.bom_line_ids.filtered(
            lambda l: l.product_id == self.component_table_leg
        )

        # 5 tops * $40 = $200; 20 legs * $5 = $100
        self.assertEqual(top_line.cost, 200.0)
        self.assertEqual(leg_line.cost, 100.0)

        # Total cost for the 5-table batch = $300.0
        self.assertEqual(bom.total_bom_cost, 300.0)

        # Cost per unit = $300.0 / 5 = $60.0
        self.assertEqual(bom.bom_cost, 60.0)

    def test_03_uom_conversion(self):
        """Test component costing when line UoM differs from product default UoM."""
        # 500 grams of powder where product base UoM is kg at $20.00/kg
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.finished_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({
                    'product_id': self.component_varnish.id,
                    'product_qty': 500.0,
                    'uom_id': self.uom_gram.id,
                }),
            ],
        })

        line = bom.bom_line_ids[0]
        # 500 g = 0.5 kg * $20.0 = $10.0
        self.assertAlmostEqual(line.cost, 10.0, places=2)
        self.assertAlmostEqual(bom.total_bom_cost, 10.0, places=2)
        self.assertAlmostEqual(bom.bom_cost, 10.0, places=2)

    def test_04_dynamic_line_update(self):
        """Test that updating component quantity recalculates line and BOM totals."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.finished_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({
                    'product_id': self.component_table_leg.id,
                    'product_qty': 4.0,
                    'uom_id': self.uom_unit.id,
                }),
            ],
        })

        line = bom.bom_line_ids[0]
        self.assertEqual(line.cost, 20.0)
        self.assertEqual(bom.total_bom_cost, 20.0)

        # Update line quantity to 8
        line.write({'product_qty': 8.0})
        self.assertEqual(line.cost, 40.0)
        self.assertEqual(bom.total_bom_cost, 40.0)
        self.assertEqual(bom.bom_cost, 40.0)

    def test_05_dynamic_product_cost_change(self):
        """Test that modifying product standard price recomputes line and BOM costs."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.finished_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({
                    'product_id': self.component_table_top.id,
                    'product_qty': 1.0,
                    'uom_id': self.uom_unit.id,
                }),
            ],
        })

        line = bom.bom_line_ids[0]
        self.assertEqual(line.cost, 40.0)

        # Change standard price from 40.0 to 50.0
        self.component_table_top.standard_price = 50.0
        self.env.flush_all()
        line._compute_cost()
        bom._compute_bom_cost()

        self.assertEqual(line.cost, 50.0)
        self.assertEqual(bom.total_bom_cost, 50.0)
        self.assertEqual(bom.bom_cost, 50.0)

    def test_06_bom_qty_change(self):
        """Test modifying BOM product_qty updates the unit cost."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.finished_product.product_tmpl_id.id,
            'product_qty': 2.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({
                    'product_id': self.component_table_top.id,
                    'product_qty': 2.0,
                    'uom_id': self.uom_unit.id,
                }),
            ],
        })

        # 2 tops @ $40 = $80 total. Unit cost = $80 / 2 = $40
        self.assertEqual(bom.total_bom_cost, 80.0)
        self.assertEqual(bom.bom_cost, 40.0)

        # Change BOM quantity to 4.0
        bom.write({'product_qty': 4.0})
        self.assertEqual(bom.total_bom_cost, 80.0)
        self.assertEqual(bom.bom_cost, 20.0)

    def test_07_multi_company_currency_fallback(self):
        """Test currency computation fallback when company_id is False."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.finished_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'company_id': False,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({
                    'product_id': self.component_table_leg.id,
                    'product_qty': 2.0,
                    'uom_id': self.uom_unit.id,
                }),
            ],
        })

        self.assertTrue(bom.currency_id)
        self.assertEqual(bom.currency_id, self.env.company.currency_id)
        self.assertEqual(bom.total_bom_cost, 10.0)

    def test_08_form_view_rendering(self):
        """Test BOM form view renders with custom cost fields."""
        bom_form = Form(self.env['mrp.bom'])
        bom_form.product_tmpl_id = self.finished_product.product_tmpl_id
        bom_form.product_qty = 2.0
        with bom_form.bom_line_ids.new() as line_form:
            line_form.product_id = self.component_table_top
            line_form.product_qty = 2.0
        bom = bom_form.save()

        self.assertEqual(bom.total_bom_cost, 80.0)
        self.assertEqual(bom.bom_cost, 40.0)
