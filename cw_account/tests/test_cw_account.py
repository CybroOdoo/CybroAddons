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
#############################################################################
from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCwAccount(TransactionCase):
    """Test suite for Catch Weight Accounting (cw_account) module.

    Covers:
    - account.move.line: cw_qty, cw_uom_id, cw_hide computed fields
    - account.move.line: _compute_cw_hide, _compute_cw_uom_id, _compute_cw_qty
    - account.move.line: _onchange_product_id_quantity, _onchange_cw_qty,
                         _onchange_product_uom_id_cw_uom_id
    - Multi-recordset batch execution
    - Edge cases (CW products vs regular products, zero average weight,
      matching vs differing UoMs, manual override of computed values)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        # Retrieve standard UoM references
        cls.uom_kg = cls.env.ref('uom.product_uom_kgm')
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        # Test partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test CW Customer',
        })

        # CW-enabled product template and variant
        cls.cw_template = cls.env['product.template'].create({
            'name': 'CW Salmon',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'catch_weigth_ok': True,
            'cw_uom_id': cls.uom_kg.id,
            'average_cw_qty': 2.5,
        })
        cls.cw_product = cls.cw_template.product_variant_ids[0]

        # CW-enabled product with same UoM (unit == unit)
        cls.cw_same_uom_template = cls.env['product.template'].create({
            'name': 'CW Box Same UoM',
            'type': 'consu',
            'uom_id': cls.uom_kg.id,
            'catch_weigth_ok': True,
            'cw_uom_id': cls.uom_kg.id,
            'average_cw_qty': 1.0,
        })
        cls.cw_same_uom_product = cls.cw_same_uom_template.product_variant_ids[0]

        # CW-enabled product with zero average_cw_qty (edge case)
        cls.cw_zero_avg_template = cls.env['product.template'].create({
            'name': 'CW Zero Avg Weight',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'catch_weigth_ok': True,
            'cw_uom_id': cls.uom_kg.id,
            'average_cw_qty': 0.0,
        })
        cls.cw_zero_avg_product = cls.cw_zero_avg_template.product_variant_ids[0]

        # Normal non-CW product
        cls.normal_template = cls.env['product.template'].create({
            'name': 'Standard Box',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'catch_weigth_ok': False,
        })
        cls.normal_product = cls.normal_template.product_variant_ids[0]

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _create_invoice(self, lines_data):
        """Helper to create a draft customer invoice with specified line data."""
        invoice_lines = [
            Command.create({
                'name': data.get('name', 'Test Line'),
                'product_id': data.get('product_id'),
                'quantity': data.get('quantity', 1.0),
                'price_unit': data.get('price_unit', 100.0),
                'product_uom_id': data.get('product_uom_id'),
            })
            for data in lines_data
        ]
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': invoice_lines,
        })

    # =========================================================================
    # 1. Computed Fields Tests
    # =========================================================================
    def test_01_cw_product_computed_fields(self):
        """Verify cw_hide, cw_uom_id, and cw_qty for a CW-enabled product."""
        move = self._create_invoice([{
            'product_id': self.cw_product.id,
            'quantity': 4.0,
            'product_uom_id': self.uom_unit.id,
        }])
        line = move.invoice_line_ids[0]

        self.assertTrue(line.cw_hide, "cw_hide must be True for CW products.")
        self.assertEqual(line.cw_uom_id, self.uom_kg, "cw_uom_id must match product's cw_uom_id.")
        # average_cw_qty (2.5) * quantity (4.0) = 10.0
        self.assertAlmostEqual(line.cw_qty, 10.0, places=4, msg="cw_qty must equal average_cw_qty * quantity.")

    def test_02_normal_product_computed_fields(self):
        """Verify cw_hide, cw_uom_id, and cw_qty for a non-CW product."""
        move = self._create_invoice([{
            'product_id': self.normal_product.id,
            'quantity': 5.0,
            'product_uom_id': self.uom_unit.id,
        }])
        line = move.invoice_line_ids[0]

        self.assertFalse(line.cw_hide, "cw_hide must be False for non-CW products.")
        self.assertFalse(line.cw_uom_id, "cw_uom_id must be False for non-CW products.")
        self.assertAlmostEqual(line.cw_qty, 0.0, places=4, msg="cw_qty must be 0.0 for non-CW products.")

    def test_03_no_product_computed_fields(self):
        """Verify computed fields when invoice line has no product."""
        move = self._create_invoice([{
            'name': 'Custom service without product',
            'product_id': False,
            'quantity': 2.0,
        }])
        line = move.invoice_line_ids[0]

        self.assertFalse(line.cw_hide, "cw_hide must be False when product is empty.")
        self.assertFalse(line.cw_uom_id, "cw_uom_id must be False when product is empty.")
        self.assertAlmostEqual(line.cw_qty, 0.0, places=4, msg="cw_qty must be 0.0 when product is empty.")

    def test_04_multi_recordset_compute(self):
        """Test multi-recordset batch computation across mixed lines."""
        move = self._create_invoice([
            {
                'product_id': self.cw_product.id,
                'quantity': 3.0,
                'product_uom_id': self.uom_unit.id,
            },
            {
                'product_id': self.normal_product.id,
                'quantity': 2.0,
                'product_uom_id': self.uom_unit.id,
            },
            {
                'product_id': False,
                'quantity': 1.0,
            },
        ])
        lines = move.invoice_line_ids

        # Trigger batch recomputations directly
        lines._compute_cw_hide()
        lines._compute_cw_uom_id()
        lines._compute_cw_qty()

        # Check line 0: CW product
        self.assertTrue(lines[0].cw_hide)
        self.assertEqual(lines[0].cw_uom_id, self.uom_kg)
        self.assertAlmostEqual(lines[0].cw_qty, 7.5, places=4)

        # Check line 1: Normal product
        self.assertFalse(lines[1].cw_hide)
        self.assertFalse(lines[1].cw_uom_id)
        self.assertAlmostEqual(lines[1].cw_qty, 0.0, places=4)

        # Check line 2: No product
        self.assertFalse(lines[2].cw_hide)
        self.assertFalse(lines[2].cw_uom_id)
        self.assertAlmostEqual(lines[2].cw_qty, 0.0, places=4)

    # =========================================================================
    # 2. Onchange Methods Tests
    # =========================================================================
    def test_05_onchange_product_id_quantity_cw_product_diff_uom(self):
        """Test _onchange_product_id_quantity when cw_uom_id != product_uom_id."""
        move = self._create_invoice([{
            'product_id': self.cw_product.id,
            'quantity': 2.0,
            'product_uom_id': self.uom_unit.id,
        }])
        line = move.invoice_line_ids[0]

        line.quantity = 6.0
        line._onchange_product_id_quantity()

        self.assertEqual(line.cw_uom_id, self.uom_kg)
        # cw_qty = average_cw_qty (2.5) * quantity (6.0) = 15.0
        self.assertAlmostEqual(line.cw_qty, 15.0, places=4)

    def test_06_onchange_product_id_quantity_cw_product_same_uom(self):
        """Test _onchange_product_id_quantity when cw_uom_id == product_uom_id."""
        move = self._create_invoice([{
            'product_id': self.cw_same_uom_product.id,
            'quantity': 1.0,
            'product_uom_id': self.uom_kg.id,
        }])
        line = move.invoice_line_ids[0]

        line.quantity = 8.5
        line._onchange_product_id_quantity()

        self.assertEqual(line.cw_uom_id, self.uom_kg)
        self.assertAlmostEqual(line.cw_qty, 8.5, places=4,
                               msg="When cw_uom_id == product_uom_id, cw_qty must sync to quantity.")

    def test_07_onchange_product_id_quantity_normal_product(self):
        """Test _onchange_product_id_quantity with non-CW product does nothing."""
        move = self._create_invoice([{
            'product_id': self.normal_product.id,
            'quantity': 3.0,
            'product_uom_id': self.uom_unit.id,
        }])
        line = move.invoice_line_ids[0]
        initial_cw_qty = line.cw_qty

        line._onchange_product_id_quantity()
        self.assertAlmostEqual(line.cw_qty, initial_cw_qty, places=4)

    def test_08_onchange_cw_qty_recalculates_quantity(self):
        """Test _onchange_cw_qty recalculating line quantity from cw_qty."""
        move = self._create_invoice([{
            'product_id': self.cw_product.id,
            'quantity': 1.0,
            'product_uom_id': self.uom_unit.id,
        }])
        line = move.invoice_line_ids[0]

        # cw_qty = 12.5, average_cw_qty = 2.5 => expected quantity = 5.0
        line.cw_qty = 12.5
        line._onchange_cw_qty()
        self.assertAlmostEqual(line.quantity, 5.0, places=4)

    def test_08b_onchange_cw_qty_same_uom_syncs_quantity(self):
        """Test _onchange_cw_qty when cw_uom_id == product_uom_id syncs quantity."""
        move = self._create_invoice([{
            'product_id': self.cw_same_uom_product.id,
            'quantity': 1.0,
            'product_uom_id': self.uom_kg.id,
        }])
        line = move.invoice_line_ids[0]

        line.cw_qty = 14.2
        line._onchange_cw_qty()
        self.assertAlmostEqual(line.quantity, 14.2, places=4)

    def test_09_onchange_cw_qty_zero_average_cw_qty(self):
        """Test _onchange_cw_qty with average_cw_qty=0 does not raise ZeroDivisionError."""
        move = self._create_invoice([{
            'product_id': self.cw_zero_avg_product.id,
            'quantity': 2.0,
            'product_uom_id': self.uom_unit.id,
        }])
        line = move.invoice_line_ids[0]

        line.cw_qty = 10.0
        # Must not raise ZeroDivisionError
        line._onchange_cw_qty()
        self.assertAlmostEqual(line.quantity, 2.0, places=4,
                               msg="Quantity must remain unchanged when average_cw_qty is 0.")

    def test_10_onchange_cw_qty_normal_product(self):
        """Test _onchange_cw_qty on a non-CW product has no effect."""
        move = self._create_invoice([{
            'product_id': self.normal_product.id,
            'quantity': 7.0,
            'product_uom_id': self.uom_unit.id,
        }])
        line = move.invoice_line_ids[0]

        line.cw_qty = 20.0
        line._onchange_cw_qty()
        self.assertAlmostEqual(line.quantity, 7.0, places=4)

    def test_11_onchange_product_uom_id_cw_uom_id_same_uom(self):
        """Test _onchange_product_uom_id_cw_uom_id when cw_uom_id == product_uom_id."""
        move = self._create_invoice([{
            'product_id': self.cw_same_uom_product.id,
            'quantity': 4.0,
            'product_uom_id': self.uom_kg.id,
        }])
        line = move.invoice_line_ids[0]

        line._onchange_product_uom_id_cw_uom_id()
        self.assertAlmostEqual(line.cw_qty, 4.0, places=4,
                               msg="When cw_uom_id == product_uom_id, cw_qty equals line quantity.")

    def test_12_onchange_product_uom_id_cw_uom_id_diff_uom(self):
        """Test _onchange_product_uom_id_cw_uom_id when cw_uom_id != product_uom_id."""
        move = self._create_invoice([{
            'product_id': self.cw_product.id,
            'quantity': 2.0,
            'product_uom_id': self.uom_unit.id,
        }])
        line = move.invoice_line_ids[0]
        initial_cw_qty = line.cw_qty

        line._onchange_product_uom_id_cw_uom_id()
        self.assertAlmostEqual(line.cw_qty, initial_cw_qty, places=4)

    def test_13_onchange_product_uom_id_cw_uom_id_normal_product(self):
        """Test _onchange_product_uom_id_cw_uom_id on a non-CW product."""
        move = self._create_invoice([{
            'product_id': self.normal_product.id,
            'quantity': 2.0,
            'product_uom_id': self.uom_unit.id,
        }])
        line = move.invoice_line_ids[0]
        initial_cw_qty = line.cw_qty

        line._onchange_product_uom_id_cw_uom_id()
        self.assertAlmostEqual(line.cw_qty, initial_cw_qty, places=4)

    # =========================================================================
    # 3. Manual Override & Persistence
    # =========================================================================
    def test_14_manual_override_stored_cw_qty(self):
        """Verify that user-provided cw_qty persists because readonly=False, store=True."""
        move = self._create_invoice([{
            'product_id': self.cw_product.id,
            'quantity': 4.0,
            'product_uom_id': self.uom_unit.id,
        }])
        line = move.invoice_line_ids[0]

        # Override cw_qty with an exact custom physical scale weight
        custom_weight = 11.2345
        line.write({'cw_qty': custom_weight})

        line.invalidate_recordset(['cw_qty'])
        self.assertAlmostEqual(line.cw_qty, custom_weight, places=4,
                               msg="Manual cw_qty override must persist in database.")

