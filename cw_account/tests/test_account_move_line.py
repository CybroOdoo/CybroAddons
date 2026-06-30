# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
"""
Tests for the Catch Weight Management: Accounting module
(account.move.line extension).

Place this file at:
    cw_account/tests/test_account_move_line.py

And make sure tests/__init__.py contains:
    from . import test_account_move_line

These tests assume the 'cw_stock' module (a dependency of this module)
defines on product.template / product.product:
    - catch_weigth_ok   (Boolean)
    - cw_uom_id         (Many2one uom.uom)
    - average_cw_qty    (Float)

If the actual field names/types differ in your cw_stock module, adjust
the setUp() product creation accordingly.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAccountMoveLineCatchWeight(TransactionCase):
    """Test cases for the catch-weight fields/logic on account.move.line."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.kg_category = cls.env.ref('uom.product_uom_categ_kgm')
        cls.uom_kg = cls.env.ref('uom.product_uom_kgm')
        cls.uom_gram = cls.env.ref('uom.product_uom_gram')
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        # Catch-weight enabled product.
        # NOTE: account.move.line._check_product_uom_category_id requires
        # product_uom_id to share the product's own UoM category, so the
        # product's base uom_id is set to kg (weight category) rather than
        # Unit, allowing lines to legitimately use kg/g on this product.
        cls.cw_product = cls.env['product.product'].create({
            'name': 'CW Test Product',
            'type': 'consu',
            'uom_id': cls.uom_kg.id,
            'uom_po_id': cls.uom_kg.id,
            'catch_weigth_ok': True,
            'cw_uom_id': cls.uom_kg.id,
            'average_cw_qty': 2.5,
        })

        # Catch-weight product whose base UoM stays "Unit", used for tests
        # that only exercise quantity/cw_qty math and don't reassign
        # product_uom_id to a different category.
        cls.cw_product_unit = cls.env['product.product'].create({
            'name': 'CW Unit-based Product',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'uom_po_id': cls.uom_unit.id,
            'catch_weigth_ok': True,
            'cw_uom_id': cls.uom_kg.id,
            'average_cw_qty': 2.5,
        })

        # Regular (non catch-weight) product, base UoM in the weight
        # category so it can also be used in the compute_weight test.
        cls.regular_product = cls.env['product.product'].create({
            'name': 'Regular Test Product',
            'type': 'consu',
            'uom_id': cls.uom_kg.id,
            'uom_po_id': cls.uom_kg.id,
            'catch_weigth_ok': False,
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)

    def _create_invoice(self):
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'invoice_date': '2025-01-01',
        })

    def _create_line(self, move, product, quantity=1.0, **extra_vals):
        vals = {
            'move_id': move.id,
            'product_id': product.id,
            'quantity': quantity,
            'price_unit': 10.0,
            'name': product.name,
        }
        vals.update(extra_vals)
        return self.env['account.move.line'].create(vals)

    # ---------------------------------------------------------------
    # _compute_hide
    # ---------------------------------------------------------------
    def test_compute_hide_true_for_catch_weight_product(self):
        """cw_hide should be True and cw_uom_id populated for a CW product."""
        move = self._create_invoice()
        line = self._create_line(move, self.cw_product)
        line._compute_hide()

        self.assertTrue(line.cw_hide)
        self.assertEqual(line.cw_uom_id, self.cw_product.cw_uom_id)

    def test_compute_hide_false_for_regular_product(self):
        """cw_hide should be False for a non catch-weight product."""
        move = self._create_invoice()
        line = self._create_line(move, self.regular_product)
        line._compute_hide()

        self.assertFalse(line.cw_hide)

    # ---------------------------------------------------------------
    # _compute_cw_qty
    # ---------------------------------------------------------------
    def test_compute_cw_qty(self):
        """cw_qty should equal average_cw_qty * quantity."""
        move = self._create_invoice()
        line = self._create_line(move, self.cw_product, quantity=4.0)
        line._compute_cw_qty()

        self.assertEqual(
            line.cw_qty, self.cw_product.average_cw_qty * 4.0)

    def test_compute_cw_qty_zero_quantity(self):
        """cw_qty should be 0 when quantity is 0."""
        move = self._create_invoice()
        line = self._create_line(move, self.cw_product, quantity=0.0)
        line._compute_cw_qty()

        self.assertEqual(line.cw_qty, 0.0)

    # ---------------------------------------------------------------
    # _onchange_product_id_qty
    # ---------------------------------------------------------------
    def test_onchange_product_qty_sets_cw_uom(self):
        """Selecting a CW product should populate cw_uom_id from the product."""
        move = self._create_invoice()
        line = self._create_line(move, self.cw_product, quantity=2.0)
        line._onchange_product_id_qty()

        self.assertEqual(line.cw_uom_id, self.cw_product.cw_uom_id)

    def test_onchange_product_qty_computes_cw_qty_when_uoms_differ(self):
        """When cw_uom_id differs from product_uom_id, cw_qty is derived
        from average_cw_qty * quantity."""
        move = self._create_invoice()
        line = self._create_line(move, self.cw_product, quantity=3.0)
        line.product_uom_id = self.uom_gram
        line.cw_uom_id = self.uom_kg
        line._onchange_product_id_qty()

        self.assertEqual(
            line.cw_qty, self.cw_product.average_cw_qty * 3.0)

    def test_onchange_product_qty_sets_quantity_when_uoms_match(self):
        """When cw_uom_id equals product_uom_id, quantity is overwritten
        by cw_qty (per current implementation)."""
        move = self._create_invoice()
        line = self._create_line(move, self.cw_product, quantity=1.0)
        line.cw_qty = 5.0
        line.product_uom_id = self.uom_kg
        line.cw_uom_id = self.uom_kg
        line._onchange_product_id_qty()

        self.assertEqual(line.quantity, 5.0)

    def test_onchange_product_qty_noop_for_regular_product(self):
        """Non catch-weight products should be left untouched."""
        move = self._create_invoice()
        line = self._create_line(move, self.regular_product, quantity=2.0)
        original_qty = line.quantity
        line._onchange_product_id_qty()

        self.assertEqual(line.quantity, original_qty)

    # ---------------------------------------------------------------
    # _onchange_cw_qty
    # ---------------------------------------------------------------
    def test_onchange_cw_qty_updates_quantity(self):
        """quantity should be recalculated as cw_qty / average_cw_qty."""
        move = self._create_invoice()
        line = self._create_line(move, self.cw_product, quantity=1.0)
        line.cw_qty = 10.0
        line._onchange_cw_qty()

        self.assertEqual(
            line.quantity, 10.0 / self.cw_product.average_cw_qty)

    def test_onchange_cw_qty_guards_against_zero_average(self):
        """If average_cw_qty is 0, quantity must not be divided by zero."""
        move = self._create_invoice()
        zero_avg_product = self.cw_product.copy({
            'name': 'CW Zero Average',
            'average_cw_qty': 0.0,
        })
        line = self._create_line(move, zero_avg_product, quantity=1.0)
        original_qty = line.quantity
        line.cw_qty = 7.0

        # Should not raise ZeroDivisionError, and quantity stays unchanged.
        line._onchange_cw_qty()
        self.assertEqual(line.quantity, original_qty)

    # ---------------------------------------------------------------
    # compute_weight
    # ---------------------------------------------------------------
    def test_compute_weight_same_category(self):
        """cw_qty should be recalculated as the factor ratio between
        cw_uom_id and product_uom_id when both share a UoM category."""
        move = self._create_invoice()
        line = self._create_line(move, self.cw_product, quantity=1.0)
        line.product_uom_id = self.uom_kg
        line.cw_uom_id = self.uom_gram
        line.compute_weight()

        self.assertEqual(
            line.cw_qty, self.uom_gram.factor / self.uom_kg.factor)

    def test_compute_weight_skipped_for_regular_product(self):
        """compute_weight should not change cw_qty for a non-CW product."""
        move = self._create_invoice()
        line = self._create_line(move, self.regular_product, quantity=1.0)
        line.product_uom_id = self.uom_kg
        line.cw_uom_id = self.uom_gram
        original_cw_qty = line.cw_qty
        line.compute_weight()

        self.assertEqual(line.cw_qty, original_cw_qty)