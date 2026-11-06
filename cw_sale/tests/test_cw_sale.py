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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCwSale(TransactionCase):
    """Test suite for the Catch Weight - Sale (cw_sale) module.

    Covers sale.order.line : is_cw_product, cw_uom_id, cw_qty, cw_delivered,
    cw_invoiced and the onchange methods.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_kg = cls.env.ref('uom.product_uom_kgm')
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.partner = cls.env['res.partner'].create({'name': 'CW Customer'})

        cls.cw_template = cls.env['product.template'].create({
            'name': 'CW Fish',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'list_price': 40.0,
            'catch_weigth_ok': True,
            'cw_uom_id': cls.uom_kg.id,
            'average_cw_qty': 2.5,
        })
        cls.cw_product = cls.cw_template.product_variant_ids[0]

        cls.normal_template = cls.env['product.template'].create({
            'name': 'Normal Box',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'list_price': 10.0,
            'catch_weigth_ok': False,
        })
        cls.normal_product = cls.normal_template.product_variant_ids[0]

        cls.same_uom_template = cls.env['product.template'].create({
            'name': 'CW Same UoM',
            'type': 'consu',
            'uom_id': cls.uom_kg.id,
            'list_price': 20.0,
            'catch_weigth_ok': True,
            'cw_uom_id': cls.uom_kg.id,
            'average_cw_qty': 1.0,
        })
        cls.same_uom_product = cls.same_uom_template.product_variant_ids[0]

        cls.zero_avg_template = cls.env['product.template'].create({
            'name': 'CW Zero Average',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'catch_weigth_ok': True,
            'cw_uom_id': cls.uom_kg.id,
            'average_cw_qty': 0.0,
        })
        cls.zero_avg_product = cls.zero_avg_template.product_variant_ids[0]

    def _make_order(self, product, qty=1.0):
        """Create a draft sale order with one line for the given product."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': qty,
            })],
        })
        return order, order.order_line[0]

    # ------------------------------------------------------------------
    # is_cw_product and cw_uom_id
    # ------------------------------------------------------------------
    def test_01_is_cw_product_true_for_cw_product(self):
        """is_cw_product must be True for a catch weight product."""
        _, line = self._make_order(self.cw_product)
        self.assertTrue(line.is_cw_product)

    def test_02_is_cw_product_false_for_normal_product(self):
        """is_cw_product must be False for a normal product."""
        _, line = self._make_order(self.normal_product)
        self.assertFalse(line.is_cw_product)

    def test_03_cw_uom_id_set_for_cw_product(self):
        """cw_uom_id must be taken from the product's CW UoM."""
        _, line = self._make_order(self.cw_product)
        self.assertEqual(line.cw_uom_id, self.uom_kg)

    def test_04_cw_uom_id_empty_for_normal_product(self):
        """cw_uom_id must be empty for a normal product."""
        _, line = self._make_order(self.normal_product)
        self.assertFalse(line.cw_uom_id)

    # ------------------------------------------------------------------
    # _onchange_product_id_product_uom_qty
    # ------------------------------------------------------------------
    def test_05_onchange_product_sets_cw_qty(self):
        """cw_qty must equal product_uom_qty x average_cw_qty when the CW UoM
        differs from the line UoM."""
        _, line = self._make_order(self.cw_product, qty=4.0)
        line._onchange_product_id_product_uom_qty()
        self.assertAlmostEqual(line.cw_qty, 4.0 * 2.5)

    def test_06_onchange_product_same_uom_cw_qty_equals_qty(self):
        """cw_qty must equal product_uom_qty when the CW UoM is the line
        UoM."""
        _, line = self._make_order(self.same_uom_product, qty=3.0)
        line._onchange_product_id_product_uom_qty()
        self.assertAlmostEqual(line.cw_qty, 3.0)

    def test_07_onchange_product_sets_price_and_uom(self):
        """The onchange must set the sales price and the CW UoM."""
        _, line = self._make_order(self.cw_product, qty=1.0)
        line.price_unit = 1.0
        line._onchange_product_id_product_uom_qty()
        self.assertAlmostEqual(line.price_unit, 40.0)
        self.assertEqual(line.cw_uom_id, self.uom_kg)

    def test_08_onchange_product_no_effect_for_normal_product(self):
        """The onchange must not change cw_qty for a normal product."""
        _, line = self._make_order(self.normal_product, qty=2.0)
        line.cw_qty = 0.0
        line._onchange_product_id_product_uom_qty()
        self.assertAlmostEqual(line.cw_qty, 0.0)

    # ------------------------------------------------------------------
    # _onchange_cw_qty
    # ------------------------------------------------------------------
    def test_09_onchange_cw_qty_updates_product_uom_qty(self):
        """Changing cw_qty must recalculate product_uom_qty."""
        _, line = self._make_order(self.cw_product, qty=1.0)
        line.cw_qty = 10.0
        line._onchange_cw_qty()
        self.assertAlmostEqual(line.product_uom_qty, 10.0 / 2.5)

    def test_10_onchange_cw_qty_same_uom(self):
        """product_uom_qty must equal cw_qty when the CW UoM is the line
        UoM."""
        _, line = self._make_order(self.same_uom_product, qty=1.0)
        line.cw_qty = 7.0
        line._onchange_cw_qty()
        self.assertAlmostEqual(line.product_uom_qty, 7.0)

    def test_11_onchange_cw_qty_no_effect_for_normal_product(self):
        """Changing cw_qty must not change the quantity of a normal
        product."""
        _, line = self._make_order(self.normal_product, qty=3.0)
        line.cw_qty = 99.0
        line._onchange_cw_qty()
        self.assertAlmostEqual(line.product_uom_qty, 3.0)

    def test_12_onchange_cw_qty_zero_average_does_not_crash(self):
        """The onchange must not raise ZeroDivisionError when the average
        catch weight is 0."""
        _, line = self._make_order(self.zero_avg_product, qty=2.0)
        line.cw_qty = 5.0
        try:
            line._onchange_cw_qty()
        except ZeroDivisionError:
            self.fail("_onchange_cw_qty raised ZeroDivisionError for avg=0")
        self.assertAlmostEqual(line.product_uom_qty, 2.0)

    # ------------------------------------------------------------------
    # cw_delivered and cw_invoiced
    # ------------------------------------------------------------------
    def test_13_cw_delivered_computed_from_qty_delivered(self):
        """cw_delivered must equal qty_delivered x average_cw_qty."""
        order, line = self._make_order(self.cw_product, qty=4.0)
        order.action_confirm()
        line.qty_delivered = 2.0
        self.assertAlmostEqual(line.cw_delivered, 2.0 * 2.5)

    def test_14_cw_invoiced_computed_from_qty_invoiced(self):
        """cw_invoiced must equal qty_invoiced x average_cw_qty."""
        self.env.company.sale_invoice_policy = 'order'
        order, line = self._make_order(self.cw_product, qty=4.0)
        order.action_confirm()
        order._create_invoices()
        self.assertAlmostEqual(line.qty_invoiced, 4.0)
        self.assertAlmostEqual(line.cw_invoiced, 4.0 * 2.5)

    def test_15_cw_delivered_invoiced_zero_before_processing(self):
        """cw_delivered and cw_invoiced must be 0 on a new order line."""
        _, line = self._make_order(self.cw_product, qty=4.0)
        self.assertAlmostEqual(line.cw_delivered, 0.0)
        self.assertAlmostEqual(line.cw_invoiced, 0.0)

    def test_16_cw_delivered_zero_for_normal_product(self):
        """cw_delivered must be 0 for a normal product."""
        order, line = self._make_order(self.normal_product, qty=4.0)
        order.action_confirm()
        line.qty_delivered = 2.0
        self.assertAlmostEqual(line.cw_delivered, 0.0)
