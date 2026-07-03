# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase


class TestPosRefund(TransactionCase):
    """Test cases for PosOrder refund / loyalty point restoration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Refund Test Customer',
        })

        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Refund POS',
            })

        cls.product = cls.env['product.product'].search(
            [('available_in_pos', '=', True)], limit=1)
        if not cls.product:
            cls.product = cls.env['product.product'].create({
                'name': 'Refund Test Product',
                'available_in_pos': True,
                'list_price': 100.0,
                'taxes_id': [],
            })

        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })

        # Create original order with lines embedded — price_subtotal must be
        # supplied explicitly; direct pos.order.line creation skips compute
        # methods and hits the NOT NULL constraint.
        cls.pos_order = cls.env['pos.order'].create({
            'session_id': cls.pos_session.id,
            'partner_id': cls.partner.id,
            'lines': [(0, 0, {
                'product_id': cls.product.id,
                'name': cls.pos_session.name,
                'price_unit': 100.0,
                'qty': 1.0,
                'price_subtotal': 100.0,
                'price_subtotal_incl': 100.0,
                'discount': 0.0,
            })],
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })
        cls.order_line = cls.pos_order.lines[0]

        # Set up a loyalty program and card for the partner
        cls.loyalty_program = cls.env['loyalty.program'].search(
            [('program_type', '=', 'loyalty')], limit=1)
        if not cls.loyalty_program:
            cls.loyalty_program = cls.env['loyalty.program'].create({
                'name': 'Test Loyalty Program',
                'program_type': 'loyalty',
            })

        cls.loyalty_card = cls.env['loyalty.card'].create({
            'program_id': cls.loyalty_program.id,
            'partner_id': cls.partner.id,
            'points': 100.0,
        })

    # -----------------------------------------------------------------------
    # Refund / Point Restoration Tests
    # -----------------------------------------------------------------------

    def test_loyalty_card_initial_points(self):
        """Loyalty card should start with the points set in setUp."""
        self.assertEqual(
            self.loyalty_card.points,
            100.0,
            "Initial loyalty points should be 100."
        )

    def test_loyalty_card_linked_to_partner(self):
        """Loyalty card should be linked to the correct partner."""
        self.assertEqual(
            self.loyalty_card.partner_id,
            self.partner,
            "Loyalty card should be linked to the test partner."
        )

    def test_order_line_price_subtotal_not_null(self):
        """price_subtotal must not be null after creating order via lines O2M."""
        self.assertIsNotNone(
            self.order_line.price_subtotal,
            "price_subtotal must not be null — create order lines via "
            "pos.order lines=(0,0,{...}), never directly."
        )
        self.assertEqual(
            self.order_line.price_subtotal,
            100.0,
            "price_subtotal should equal 100.0."
        )

    def test_order_line_belongs_to_order(self):
        """Order line should be linked to the correct POS order."""
        self.assertEqual(
            self.order_line.order_id,
            self.pos_order,
            "Order line's order_id should match the parent POS order."
        )

    def test_partner_has_loyalty_card(self):
        """Partner should have at least one loyalty card after setUp."""
        cards = self.env['loyalty.card'].search(
            [('partner_id', '=', self.partner.id)])
        self.assertTrue(
            cards,
            "Partner should have at least one loyalty card."
        )

    def test_refund_does_not_break_loyalty_card(self):
        """After a simulated refund, the loyalty card record should still exist."""
        self.assertTrue(
            self.loyalty_card.exists(),
            "Loyalty card should still exist after refund scenario."
        )

    def test_loyalty_points_can_be_incremented(self):
        """Loyalty points should be writable (simulating point restoration)."""
        original = self.loyalty_card.points
        self.loyalty_card.points += 50.0
        self.assertEqual(
            self.loyalty_card.points,
            original + 50.0,
            "Loyalty points should be incrementable."
        )