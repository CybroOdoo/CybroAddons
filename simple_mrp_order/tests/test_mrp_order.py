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
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestSimpleMRPOrder(common.TransactionCase):
    """Test suite for Simple Manufacturing Orders (simple_mrp_order)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1
        )
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.prod_loc = cls.env.ref('simple_mrp_order.location_simple_mrp')
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        # Create finished product
        cls.finished_product = cls.env['product.product'].create({
            'name': 'Dining Table Test',
            'is_storable': True,
            'uom_id': cls.uom_unit.id,
        })

        # Create component products
        cls.component_top = cls.env['product.product'].create({
            'name': 'Table Top Test',
            'is_storable': True,
            'uom_id': cls.uom_unit.id,
        })
        cls.component_leg = cls.env['product.product'].create({
            'name': 'Table Leg Test',
            'is_storable': True,
            'uom_id': cls.uom_unit.id,
        })

        # Create Bill of Materials
        cls.bom = cls.env['simple.mrp.bom'].create({
            'product_id': cls.finished_product.id,
            'product_qty': 1.0,
            'uom_id': cls.uom_unit.id,
            'company_id': cls.company.id,
            'line_ids': [
                fields.Command.create({
                    'product_id': cls.component_top.id,
                    'product_qty': 1.0,
                    'uom_id': cls.uom_unit.id,
                }),
                fields.Command.create({
                    'product_id': cls.component_leg.id,
                    'product_qty': 4.0,
                    'uom_id': cls.uom_unit.id,
                }),
            ],
        })

    def test_01_bom_creation_and_onchanges(self):
        """Test Bill of Materials creation and onchange triggers."""
        self.assertEqual(self.bom.product_id, self.finished_product)
        self.assertEqual(len(self.bom.line_ids), 2)
        self.assertEqual(self.bom.product_qty, 1.0)

        # Test onchange on simple.mrp.bom
        new_bom = self.env['simple.mrp.bom'].new({'product_id': self.finished_product.id})
        new_bom._onchange_product_id()
        self.assertEqual(new_bom.uom_id, self.finished_product.uom_id)

        # Test onchange on simple.mrp.bom.line
        new_line = self.env['simple.mrp.bom.line'].new({'product_id': self.component_top.id})
        new_line._onchange_product_id()
        self.assertEqual(new_line.uom_id, self.component_top.uom_id)

    def test_02_order_creation_and_component_recalculation(self):
        """Test manufacturing order creation and dynamic component recalculation."""
        order = self.env['mrp.order'].new({'product_id': self.finished_product.id})
        order._onchange_product_id()
        self.assertEqual(order.uom_id, self.finished_product.uom_id)
        self.assertEqual(order.bom_id, self.bom)

        # Recalculate components for 1 unit
        order.product_qty = 1.0
        order._onchange_bom_id()
        self.assertEqual(len(order.line_ids), 2)
        self.assertEqual(len(order.stock_line_ids), 2)

        # Change quantity to 3 units and verify multiplication
        order.product_qty = 3.0
        order._onchange_bom_id()
        top_move = next(line for line in order.stock_line_ids if line.product_id == self.component_top)
        leg_move = next(line for line in order.stock_line_ids if line.product_id == self.component_leg)
        self.assertEqual(top_move.product_uom_qty, 3.0)
        self.assertEqual(leg_move.product_uom_qty, 12.0)

        # Test UoM onchange
        order._onchange_uom_id()
        self.assertEqual(len(order.line_ids), 2)
        self.assertEqual(len(order.stock_line_ids), 2)

        # Persist the order in the database
        created_order = self.env['mrp.order'].create({
            'product_id': self.finished_product.id,
            'product_qty': 2.0,
            'uom_id': self.uom_unit.id,
            'bom_id': self.bom.id,
            'company_id': self.company.id,
            'location_src_id': self.stock_loc.id,
            'stock_line_ids': [
                fields.Command.create({
                    'product_id': self.component_top.id,
                    'product_uom_qty': 2.0,
                    'uom_id': self.uom_unit.id,
                    'location_id': self.stock_loc.id,
                    'location_dest_id': self.prod_loc.id,
                }),
                fields.Command.create({
                    'product_id': self.component_leg.id,
                    'product_uom_qty': 8.0,
                    'uom_id': self.uom_unit.id,
                    'location_id': self.stock_loc.id,
                    'location_dest_id': self.prod_loc.id,
                }),
            ],
        })
        self.assertTrue(created_order.name.startswith('MRP/'))
        self.assertEqual(created_order.state, 'draft')

        # Test write override updating stock lines
        created_order.write({
            'product_qty': 4.0,
            'stock_line_ids': [
                fields.Command.clear(),
                fields.Command.create({
                    'product_id': self.component_top.id,
                    'product_uom_qty': 4.0,
                    'uom_id': self.uom_unit.id,
                }),
            ],
        })
        self.assertEqual(len(created_order.stock_line_ids), 1)
        self.assertEqual(created_order.stock_line_ids.location_id, self.stock_loc)
        self.assertEqual(created_order.stock_line_ids.location_dest_id, self.prod_loc)

    def test_03_low_stock_validation(self):
        """Test low-stock validation blocks confirmation with a ValidationError."""
        order = self.env['mrp.order'].create({
            'product_id': self.finished_product.id,
            'product_qty': 10.0,
            'uom_id': self.uom_unit.id,
            'bom_id': self.bom.id,
            'company_id': self.company.id,
            'location_src_id': self.stock_loc.id,
            'stock_line_ids': [
                fields.Command.create({
                    'product_id': self.component_top.id,
                    'product_uom_qty': 10.0,
                    'uom_id': self.uom_unit.id,
                }),
            ],
        })
        # Currently 0 stock available for component_top
        with self.assertRaises(ValidationError):
            order.action_confirm()
        self.assertEqual(order.state, 'draft')

    def test_04_successful_confirmation_and_completion(self):
        """Test complete production happy path, inventory movements, and smart button."""
        # Add stock for raw materials
        self.env['stock.quant']._update_available_quantity(
            self.component_top, self.stock_loc, 10.0
        )
        self.env['stock.quant']._update_available_quantity(
            self.component_leg, self.stock_loc, 40.0
        )

        order = self.env['mrp.order'].create({
            'product_id': self.finished_product.id,
            'product_qty': 2.0,
            'uom_id': self.uom_unit.id,
            'bom_id': self.bom.id,
            'company_id': self.company.id,
            'location_src_id': self.stock_loc.id,
            'stock_line_ids': [
                fields.Command.create({
                    'product_id': self.component_top.id,
                    'product_uom_qty': 2.0,
                    'uom_id': self.uom_unit.id,
                }),
                fields.Command.create({
                    'product_id': self.component_leg.id,
                    'product_uom_qty': 8.0,
                    'uom_id': self.uom_unit.id,
                }),
            ],
        })

        # Confirm order
        order.action_confirm()
        self.assertEqual(order.state, 'confirmed')

        # Complete production
        order.action_done()
        self.assertEqual(order.state, 'done')

        # Verify component consumption moves (WH/Stock -> Simple Production)
        for move in order.stock_line_ids:
            self.assertEqual(move.state, 'done')
            self.assertEqual(move.location_id, self.stock_loc)
            self.assertEqual(move.location_dest_id, self.prod_loc)

        # Verify finished good production move (Simple Production -> WH/Stock)
        finished_move = order.stock_move_id
        self.assertTrue(finished_move)
        self.assertEqual(finished_move.state, 'done')
        self.assertEqual(finished_move.product_id, self.finished_product)
        self.assertEqual(finished_move.product_uom_qty, 2.0)
        self.assertEqual(finished_move.location_id, self.prod_loc)
        self.assertEqual(finished_move.location_dest_id, self.stock_loc)

        # Test smart button action
        action = order.action_view_move()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'stock.move')
        expected_ids = order.stock_line_ids.ids + [finished_move.id]
        self.assertEqual(action.get('domain'), [('id', 'in', expected_ids)])

    def test_05_order_cancellation(self):
        """Test order cancellation from confirmed state."""
        self.env['stock.quant']._update_available_quantity(
            self.component_top, self.stock_loc, 5.0
        )
        self.env['stock.quant']._update_available_quantity(
            self.component_leg, self.stock_loc, 20.0
        )

        order = self.env['mrp.order'].create({
            'product_id': self.finished_product.id,
            'product_qty': 1.0,
            'uom_id': self.uom_unit.id,
            'bom_id': self.bom.id,
            'company_id': self.company.id,
            'location_src_id': self.stock_loc.id,
            'stock_line_ids': [
                fields.Command.create({
                    'product_id': self.component_top.id,
                    'product_uom_qty': 1.0,
                    'uom_id': self.uom_unit.id,
                }),
                fields.Command.create({
                    'product_id': self.component_leg.id,
                    'product_uom_qty': 4.0,
                    'uom_id': self.uom_unit.id,
                }),
            ],
        })
        order.action_confirm()
        self.assertEqual(order.state, 'confirmed')

        order.action_cancel()
        self.assertEqual(order.state, 'cancel')

    def test_06_multi_record_support(self):
        """Test multi-recordset operations across orders."""
        order1 = self.env['mrp.order'].create({
            'product_id': self.finished_product.id,
            'product_qty': 1.0,
            'uom_id': self.uom_unit.id,
            'company_id': self.company.id,
        })
        order2 = self.env['mrp.order'].create({
            'product_id': self.finished_product.id,
            'product_qty': 2.0,
            'uom_id': self.uom_unit.id,
            'company_id': self.company.id,
        })
        orders = order1 | order2
        # Test multi-record write
        orders.write({'location_src_id': self.stock_loc.id})
        self.assertEqual(order1.location_src_id, self.stock_loc)
        self.assertEqual(order2.location_src_id, self.stock_loc)

        # Test multi-record cancel
        orders.action_cancel()
        self.assertEqual(order1.state, 'cancel')
        self.assertEqual(order2.state, 'cancel')

    def test_07_default_location_helper(self):
        """Test default source location helper method."""
        default_loc_id = self.env['mrp.order']._get_default_location_src_id()
        self.assertTrue(default_loc_id)
        self.assertEqual(default_loc_id, self.stock_loc.id)