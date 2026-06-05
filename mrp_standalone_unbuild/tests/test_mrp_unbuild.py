# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests import Form, tagged
from odoo.addons.mrp.tests.common import TestMrpCommon


@tagged('post_install', '-at_install')
class TestMrpUnbuild(TestMrpCommon):
    """Tests for the MrpUnbuild model (models/mrp_unbuild.py)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.unit_uom = cls.env.ref('uom.product_uom_unit')
        cls.stock_quant = cls.env['stock.quant']

        cls.finished_product = cls.env['product.product'].create({
            'name': 'MrpUnbuild Finished Product',
            'type': 'consu',
            'is_storable': True,
        })
        cls.component_a = cls.env['product.product'].create({
            'name': 'MrpUnbuild Component A',
            'type': 'consu',
            'is_storable': True,
        })
        cls.component_b = cls.env['product.product'].create({
            'name': 'MrpUnbuild Component B',
            'type': 'consu',
            'is_storable': True,
        })
        cls.byproduct_product = cls.env['product.product'].create({
            'name': 'MrpUnbuild Byproduct',
            'type': 'consu',
            'is_storable': True,
        })

        cls.bom = cls.env['mrp.bom'].create({
            'product_id': cls.finished_product.id,
            'product_tmpl_id': cls.finished_product.product_tmpl_id.id,
            'product_uom_id': cls.unit_uom.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {'product_id': cls.component_a.id, 'product_qty': 2.0}),
                (0, 0, {'product_id': cls.component_b.id, 'product_qty': 3.0}),
            ],
        })
        cls.byproduct_line = cls.env['mrp.bom.byproduct'].create({
            'bom_id': cls.bom.id,
            'product_id': cls.byproduct_product.id,
            'product_qty': 1.0,
            'product_uom_id': cls.unit_uom.id,
        })

    def _make_unbuild(self, product_qty=1.0):
        """Helper to create a standalone unbuild order using the Form."""
        unbuild_form = Form(self.env['mrp.unbuild'])
        unbuild_form.product_id = self.finished_product
        unbuild_form.bom_id = self.bom
        unbuild_form.product_qty = product_qty
        unbuild_form.location_id = self.stock_location
        unbuild_form.location_dest_id = self.stock_location
        return unbuild_form.save()

    def test_onchange_bom_populates_component_lines(self):
        """Test that selecting a BOM auto-populates all component + byproduct lines"""
        unbuild = self._make_unbuild(product_qty=1.0)
        self.assertEqual(len(unbuild.unbuild_line_ids), 3)

        products_in_lines = unbuild.unbuild_line_ids.mapped('product_id')
        self.assertIn(self.component_a, products_in_lines)
        self.assertIn(self.component_b, products_in_lines)
        self.assertIn(self.byproduct_product, products_in_lines)

    def test_onchange_bom_scales_quantities_by_product_qty(self):
        """Test that quantities in unbuild lines scale proportionally with product_qty"""
        unbuild = self._make_unbuild(product_qty=3.0)

        qty_map = {line.product_id: line.qty for line in unbuild.unbuild_line_ids}
        self.assertEqual(qty_map[self.component_a], 6.0)
        self.assertEqual(qty_map[self.component_b], 9.0)
        self.assertEqual(qty_map[self.byproduct_product], 3.0)

    def test_onchange_clear_bom_clears_lines(self):
        """Test that removing the BOM clears all unbuild lines"""
        unbuild_form = Form(self.env['mrp.unbuild'])
        unbuild_form.product_id = self.finished_product
        unbuild_form.bom_id = self.bom
        unbuild_form.product_qty = 1.0
        unbuild_form.location_id = self.stock_location
        unbuild_form.location_dest_id = self.stock_location
        unbuild_form.bom_id = self.env['mrp.bom']
        unbuild = unbuild_form.save()

        self.assertEqual(len(unbuild.unbuild_line_ids), 0)

    def test_standalone_action_unbuild_state_becomes_done(self):
        """Test that action_unbuild (without mo_id) transitions state to done"""
        self.stock_quant._update_available_quantity(
            self.finished_product, self.stock_location, 2.0
        )
        unbuild = self._make_unbuild(product_qty=2.0)
        unbuild.action_unbuild()

        self.assertEqual(unbuild.state, 'done')

    def test_standalone_action_unbuild_consumes_finished_stock(self):
        """Test that action_unbuild consumes the finished product from stock"""
        self.stock_quant._update_available_quantity(
            self.finished_product, self.stock_location, 1.0
        )
        unbuild = self._make_unbuild(product_qty=1.0)
        unbuild.action_unbuild()

        remaining = self.stock_quant._get_available_quantity(
            self.finished_product, self.stock_location
        )
        self.assertEqual(remaining, 0.0)

    def test_standalone_action_unbuild_produces_component_stock(self):
        """Test that action_unbuild returns component quantities to destination location"""
        self.stock_quant._update_available_quantity(
            self.finished_product, self.stock_location, 2.0
        )
        unbuild = self._make_unbuild(product_qty=2.0)
        unbuild.action_unbuild()

        comp_a_qty = self.stock_quant._get_available_quantity(
            self.component_a, self.stock_location
        )
        comp_b_qty = self.stock_quant._get_available_quantity(
            self.component_b, self.stock_location
        )
        byproduct_qty = self.stock_quant._get_available_quantity(
            self.byproduct_product, self.stock_location
        )
        self.assertEqual(comp_a_qty, 4.0)
        self.assertEqual(comp_b_qty, 6.0)
        self.assertEqual(byproduct_qty, 2.0)

    def test_action_unbuild_tracked_product_without_lot_raises(self):
        """Test ValidationError when unbuilding a lot-tracked product without a lot"""
        tracked_product = self.env['product.product'].create({
            'name': 'Tracked Finished Product',
            'type': 'consu',
            'is_storable': True,
            'tracking': 'lot',
        })
        tracked_bom = self.env['mrp.bom'].create({
            'product_id': tracked_product.id,
            'product_tmpl_id': tracked_product.product_tmpl_id.id,
            'product_uom_id': self.unit_uom.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {'product_id': self.component_a.id, 'product_qty': 1.0}),
            ],
        })

        unbuild = self.env['mrp.unbuild'].create({
            'product_id': tracked_product.id,
            'bom_id': tracked_bom.id,
            'product_qty': 1.0,
            'product_uom_id': self.unit_uom.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.stock_location.id,
        })

        with self.assertRaises(Exception):
            unbuild.action_unbuild()

    def test_generate_consume_moves_creates_single_finished_move(self):
        """Test _generate_consume_moves returns one move for the finished product"""
        self.stock_quant._update_available_quantity(
            self.finished_product, self.stock_location, 1.0
        )
        unbuild = self._make_unbuild(product_qty=1.0)
        consume_moves = unbuild._generate_consume_moves()

        # Should have exactly one move - the finished product consume move
        self.assertEqual(len(consume_moves), 1)
        self.assertEqual(consume_moves.product_id, self.finished_product)

    def test_generate_produce_moves_creates_moves_for_each_line(self):
        """Test _generate_produce_moves creates a stock.move for every unbuild line"""
        unbuild = self._make_unbuild(product_qty=1.0)
        # BOM: 2 components + 1 byproduct = 3 unbuild_line_ids
        self.assertEqual(len(unbuild.unbuild_line_ids), 3)

        produce_moves = unbuild._generate_produce_moves()
        # Each line should produce a stock move
        self.assertEqual(len(produce_moves), len(unbuild.unbuild_line_ids))
        produced_products = produce_moves.mapped('product_id')
        self.assertIn(self.component_a, produced_products)
        self.assertIn(self.component_b, produced_products)
        self.assertIn(self.byproduct_product, produced_products)
