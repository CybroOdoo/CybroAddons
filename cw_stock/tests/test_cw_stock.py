# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)

#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCwStock(TransactionCase):
    """Test suite for the Catch Weight Stock (cw_stock) module.

    Covers:
    - product.template  : apply_cw, cw_uom_id, catch_weigth_ok,
                          average_cw_qty, _onchange_cw_uom_id
    - stock.move        : cw_hide, cw_demand, cw_reserved, cw_done,
                          _compute_hide, _compute_cw_demand, onchange methods
    - stock.move.line   : cw_qty_done, cw_uom_id, cw_hide computed fields
    - scrap moves       : stock.move with is_scrap=True (stock.scrap no longer
                          exists in Odoo 20)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # UoM records
        cls.uom_kg = cls.env.ref('uom.product_uom_kgm')
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        # CW-enabled product template + product
        cls.cw_template = cls.env['product.template'].create({
            'name': 'CW Fish',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'catch_weigth_ok': True,
            'cw_uom_id': cls.uom_kg.id,
            'average_cw_qty': 2.5,
        })
        cls.cw_product = cls.cw_template.product_variant_ids[0]

        # Regular (non-CW) product
        cls.normal_template = cls.env['product.template'].create({
            'name': 'Normal Box',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'catch_weigth_ok': False,
        })
        cls.normal_product = cls.normal_template.product_variant_ids[0]

        # Stock locations & picking type for creating moves
        cls.location_src = cls.env.ref('stock.stock_location_stock')
        cls.location_dest = cls.env.ref('stock.stock_location_customers')
        cls.picking_type_out = cls.env.ref('stock.picking_type_out')

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def _make_picking(self, product, qty=1.0):
        """Create a confirmed outgoing picking with one move."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        move = self.env['stock.move'].create({
            'description_picking': product.name,
            'picking_id': picking.id,
            'product_id': product.id,
            'uom_id': product.uom_id.id,
            'product_uom_qty': qty,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        move._action_confirm()
        return picking, move

    # ==================================================================
    # 1.  product.template — custom fields
    # ==================================================================
    def test_01_product_catch_weigth_ok_stored(self):
        """catch_weigth_ok must persist as True on a CW product."""
        self.assertTrue(self.cw_template.catch_weigth_ok)

    def test_02_product_catch_weigth_ok_default_false(self):
        """catch_weigth_ok must default to False on a normal product."""
        self.assertFalse(self.normal_template.catch_weigth_ok)

    def test_03_product_cw_uom_id_stored(self):
        """cw_uom_id must be saved and point to the correct UoM."""
        self.assertEqual(self.cw_template.cw_uom_id, self.uom_kg)

    def test_04_product_average_cw_qty_stored(self):
        """average_cw_qty must persist with the value set at creation."""
        self.assertAlmostEqual(self.cw_template.average_cw_qty, 2.5)

    def test_05_product_apply_cw_field_writable(self):
        """apply_cw flag must be writable and readable."""
        self.cw_template.apply_cw = True
        self.assertTrue(self.cw_template.apply_cw)

    def test_06_onchange_cw_uom_same_category_sets_factor(self):
        """_onchange_cw_uom_id: when uom_id == cw_uom_id, average_cw_qty
        should be set to cw_uom_id.factor / uom_id.factor (= 1.0 for same UoM)."""
        tmpl = self.env['product.template'].create({
            'name': 'Same UoM CW',
            'type': 'consu',
            'uom_id': self.uom_kg.id,
            'cw_uom_id': self.uom_kg.id,
            'catch_weigth_ok': True,
        })
        tmpl._onchange_cw_uom_id()
        expected = self.uom_kg.factor / self.uom_kg.factor
        self.assertAlmostEqual(tmpl.average_cw_qty, expected)

    def test_07_onchange_cw_uom_different_uom_sets_one(self):
        """_onchange_cw_uom_id: when uom_id != cw_uom_id, average_cw_qty
        must be reset to 1.0."""
        tmpl = self.env['product.template'].create({
            'name': 'Diff UoM CW',
            'type': 'consu',
            'uom_id': self.uom_unit.id,
            'cw_uom_id': self.uom_kg.id,
            'catch_weigth_ok': True,
        })
        tmpl._onchange_cw_uom_id()
        self.assertAlmostEqual(tmpl.average_cw_qty, 1.0)

    # ==================================================================
    # 2.  stock.move — computed fields
    # ==================================================================
    def test_08_stock_move_cw_hide_true_for_cw_product(self):
        """cw_hide must be True when the product has catch_weigth_ok=True."""
        _, move = self._make_picking(self.cw_product, qty=4.0)
        self.assertTrue(move.cw_hide)

    def test_09_stock_move_cw_hide_false_for_normal_product(self):
        """cw_hide must be False for a product with catch_weigth_ok=False."""
        _, move = self._make_picking(self.normal_product, qty=4.0)
        self.assertFalse(move.cw_hide)

    def test_10_stock_move_cw_demand_computed(self):
        """cw_demand must equal product_uom_qty × average_cw_qty."""
        _, move = self._make_picking(self.cw_product, qty=4.0)
        move._compute_cw_demand()
        expected = 4.0 * self.cw_template.average_cw_qty  # 4 × 2.5 = 10.0
        self.assertAlmostEqual(move.cw_demand, expected)

    def test_11_stock_move_cw_reserved_equals_demand(self):
        """cw_reserved must equal product_uom_qty × average_cw_qty."""
        _, move = self._make_picking(self.cw_product, qty=3.0)
        move._compute_cw_demand()
        expected = 3.0 * self.cw_template.average_cw_qty  # 3 × 2.5 = 7.5
        self.assertAlmostEqual(move.cw_reserved, expected)

    def test_12_stock_move_cw_uom_set_by_cal(self):
        """_compute_cw_demand must set cw_uom_id from the product's cw_uom_id."""
        _, move = self._make_picking(self.cw_product, qty=1.0)
        move._compute_cw_demand()
        self.assertEqual(move.cw_uom_id, self.uom_kg)

    def test_13_stock_move_cw_done_computed_from_quantity(self):
        """cw_done must equal move.quantity × average_cw_qty after _compute_cw_demand."""
        _, move = self._make_picking(self.cw_product, qty=2.0)
        move.quantity = 2.0
        move._compute_cw_demand()
        expected = 2.0 * self.cw_template.average_cw_qty  # 2 × 2.5 = 5.0
        self.assertAlmostEqual(move.cw_done, expected)

    def test_14_onchange_cw_done_updates_quantity(self):
        """_onchange_cw_done: setting cw_done must back-calculate quantity."""
        _, move = self._make_picking(self.cw_product, qty=1.0)
        move.cw_done = 5.0        # 5 kg ÷ 2.5 avg = 2 units
        move._onchange_cw_done()
        expected = 5.0 / self.cw_template.average_cw_qty
        self.assertAlmostEqual(move.quantity, expected)

    def test_15_onchange_cw_done_no_effect_for_normal_product(self):
        """_onchange_cw_done must not change quantity for non-CW products."""
        _, move = self._make_picking(self.normal_product, qty=3.0)
        move.quantity = 3.0
        move.cw_done = 99.0
        move._onchange_cw_done()
        # quantity must remain unchanged for non-CW products
        self.assertAlmostEqual(move.quantity, 3.0)

    def test_16_onchange_cw_demand_updates_product_uom_qty(self):
        """_onchange_cw_demand: changing cw_demand must recalculate product_uom_qty."""
        _, move = self._make_picking(self.cw_product, qty=1.0)
        move._compute_cw_demand()
        move.cw_demand = 10.0    # 10 kg ÷ 2.5 avg = 4 units
        move._onchange_cw_demand()
        expected = 10.0 / self.cw_template.average_cw_qty
        self.assertAlmostEqual(move.product_uom_qty, expected)

    def test_17_onchange_product_id_sets_cw_demand_and_uom(self):
        """_onchange_product_id must set cw_demand and cw_uom_id for CW product."""
        _, move = self._make_picking(self.cw_product, qty=3.0)
        move._onchange_product_id()
        self.assertAlmostEqual(
            move.cw_demand, 3.0 * self.cw_template.average_cw_qty)
        self.assertEqual(move.cw_uom_id, self.uom_kg)

    def test_18_onchange_product_id_clears_cw_uom_for_normal_product(self):
        """_onchange_product_id must clear cw_uom_id for a non-CW product."""
        _, move = self._make_picking(self.normal_product, qty=2.0)
        move._onchange_product_id()
        self.assertFalse(move.cw_uom_id)

    def test_19_compute_cw_demand_zero_avg_does_not_crash(self):
        """_compute_cw_demand must handle average_cw_qty=0 without raising."""
        tmpl = self.env['product.template'].create({
            'name': 'Zero Avg CW',
            'type': 'consu',
            'uom_id': self.uom_unit.id,
            'catch_weigth_ok': True,
            'cw_uom_id': self.uom_kg.id,
            'average_cw_qty': 0.0,
        })
        product = tmpl.product_variant_ids[0]
        _, move = self._make_picking(product, qty=2.0)
        # Should not raise
        try:
            move._compute_cw_demand()
        except ZeroDivisionError:
            self.fail("_compute_cw_demand raised ZeroDivisionError for avg=0")

    # ==================================================================
    # 3.  stock.move.line — computed fields
    # ==================================================================
    def test_20_move_line_cw_hide_true_for_cw_product(self):
        """cw_hide on move line must be True for a CW product."""
        picking, move = self._make_picking(self.cw_product, qty=2.0)
        move.quantity = 2.0
        line = move.move_line_ids[:1] or self.env['stock.move.line'].create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': self.cw_product.id,
            'uom_id': self.uom_unit.id,
            'quantity': 2.0,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        self.assertTrue(line.cw_hide)

    def test_21_move_line_cw_hide_false_for_normal_product(self):
        """cw_hide on move line must be False for a non-CW product."""
        picking, move = self._make_picking(self.normal_product, qty=2.0)
        line = self.env['stock.move.line'].create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': self.normal_product.id,
            'uom_id': self.uom_unit.id,
            'quantity': 2.0,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        self.assertFalse(line.cw_hide)

    def test_22_move_line_cw_uom_id_set_for_cw_product(self):
        """cw_uom_id on move line must match the product's cw_uom_id."""
        picking, move = self._make_picking(self.cw_product, qty=1.0)
        line = self.env['stock.move.line'].create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': self.cw_product.id,
            'uom_id': self.uom_unit.id,
            'quantity': 1.0,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        self.assertEqual(line.cw_uom_id, self.uom_kg)

    def test_23_move_line_cw_uom_id_empty_for_normal_product(self):
        """cw_uom_id on move line must be empty for a non-CW product."""
        picking, move = self._make_picking(self.normal_product, qty=1.0)
        line = self.env['stock.move.line'].create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': self.normal_product.id,
            'uom_id': self.uom_unit.id,
            'quantity': 1.0,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        self.assertFalse(line.cw_uom_id)

    def test_24_move_line_cw_qty_done_computed_correctly(self):
        """cw_qty_done must equal quantity × average_cw_qty for CW products."""
        picking, move = self._make_picking(self.cw_product, qty=3.0)
        line = self.env['stock.move.line'].create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': self.cw_product.id,
            'uom_id': self.uom_unit.id,
            'quantity': 3.0,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        expected = 3.0 * self.cw_template.average_cw_qty  # 3 × 2.5 = 7.5
        self.assertAlmostEqual(line.cw_qty_done, expected)

    def test_25_move_line_cw_qty_done_zero_for_normal_product(self):
        """cw_qty_done must be 0 for non-CW products."""
        picking, move = self._make_picking(self.normal_product, qty=5.0)
        line = self.env['stock.move.line'].create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': self.normal_product.id,
            'uom_id': self.uom_unit.id,
            'quantity': 5.0,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        self.assertAlmostEqual(line.cw_qty_done, 0.0)

    # ==================================================================
    # 4.  Scrap moves (stock.move with is_scrap=True)
    # ==================================================================
    def _make_scrap_move(self, product, qty=1.0):
        """Create a scrap stock.move for the given product."""
        scrap_location = self.env['stock.location'].search(
            [('usage', '=', 'inventory')], limit=1)
        return self.env['stock.move'].create({
            'product_id': product.id,
            'uom_id': product.uom_id.id,
            'product_uom_qty': qty,
            'quantity': qty,
            'is_scrap': True,
            'location_id': self.location_src.id,
            'location_dest_id': scrap_location.id,
        })

    def test_26_scrap_move_cw_hide_true_for_cw_product(self):
        """cw_hide on a scrap move must be True for a CW product."""
        move = self._make_scrap_move(self.cw_product, qty=2.0)
        self.assertTrue(move.cw_hide)

    def test_27_scrap_move_cw_hide_false_for_normal_product(self):
        """cw_hide on a scrap move must be False for a non-CW product."""
        move = self._make_scrap_move(self.normal_product, qty=2.0)
        self.assertFalse(move.cw_hide)

    def test_28_scrap_move_cw_done_computed_from_quantity(self):
        """cw_done on a scrap move must equal quantity × average_cw_qty."""
        move = self._make_scrap_move(self.cw_product, qty=4.0)
        move._compute_cw_demand()
        expected = 4.0 * self.cw_template.average_cw_qty  # 4 × 2.5 = 10.0
        self.assertAlmostEqual(move.cw_done, expected)
        self.assertEqual(move.cw_uom_id, self.uom_kg)
