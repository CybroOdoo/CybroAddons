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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestBomCost(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBomCost, cls).setUpClass()

        # Create finished product
        cls.product_finished = cls.env['product.product'].create({
            'name': 'Finished Product',
            'type': 'consu',
        })

        # Create raw materials / components
        cls.component_1 = cls.env['product.product'].create({
            'name': 'Component 1',
            'type': 'consu',
            'standard_price': 10.0,
        })

        cls.component_2 = cls.env['product.product'].create({
            'name': 'Component 2',
            'type': 'consu',
            'standard_price': 20.0,
        })

    def test_01_bom_cost_calculation(self):
        """Test that BOM cost and total BOM cost are computed correctly with lines."""
        # Create a Bill of Materials with 2 components
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_finished.product_tmpl_id.id,
            'product_qty': 2.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.component_1.id,
                    'product_qty': 3.0,
                }),
                (0, 0, {
                    'product_id': self.component_2.id,
                    'product_qty': 5.0,
                })
            ]
        })

        # Verify that the individual BOM line costs are computed correctly:
        # component_1: 10.0 * 3.0 = 30.0
        # component_2: 20.0 * 5.0 = 100.0
        bom_lines = bom.bom_line_ids
        self.assertEqual(bom_lines[0].cost, 30.0, "Cost of component 1 line should be 30.0")
        self.assertEqual(bom_lines[1].cost, 100.0, "Cost of component 2 line should be 100.0")

        # Verify that the BOM cost (per unit) and total BOM cost are computed correctly:
        # Cost Per Unit = 30.0 + 100.0 = 130.0
        # Total Cost = 130.0 * 2.0 (BOM product_qty) = 260.0
        self.assertEqual(bom.bom_cost, 130.0, "BOM cost per unit should be 130.0")
        self.assertEqual(bom.total_bom_cost, 260.0, "Total BOM cost should be 260.0")

    def test_02_bom_cost_on_bom_qty_change(self):
        """Test that modifying the BOM quantity updates the total BOM cost."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_finished.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.component_1.id,
                    'product_qty': 2.0,
                })
            ]
        })

        self.assertEqual(bom.bom_cost, 20.0)
        self.assertEqual(bom.total_bom_cost, 20.0)

        # Update the BOM product quantity to 3.0
        bom.write({'product_qty': 3.0})

        # Total Cost should update to 20.0 * 3.0 = 60.0
        self.assertEqual(bom.total_bom_cost, 60.0, "Total BOM cost should update when BOM quantity is changed")

    def test_03_bom_line_cost_calculation(self):
        """Test the computation of mrp.bom.line cost field."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_finished.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.component_2.id,
                    'product_qty': 4.0,
                })
            ]
        })

        line = bom.bom_line_ids[0]
        self.assertEqual(line.cost, 80.0, "BOM line cost should be product standard price multiplied by quantity")
