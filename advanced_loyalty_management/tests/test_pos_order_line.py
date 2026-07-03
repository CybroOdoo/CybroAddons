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


class TestPosOrderLine(TransactionCase):
    """Test cases for PosOrderLine model (advanced_loyalty_management)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Loyalty Customer',
        })

        # Locate an open POS config (or the first available one)
        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Test POS',
            })

        # Find a usable product
        cls.product = cls.env['product.product'].search(
            [('available_in_pos', '=', True)], limit=1)
        if not cls.product:
            cls.product = cls.env['product.product'].create({
                'name': 'Test POS Product',
                'available_in_pos': True,
                'list_price': 100.0,
                'taxes_id': [],
            })

        # Open a POS session so orders can be created
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })

        # Create a POS order with lines embedded — never create pos.order.line
        # directly; price_subtotal and other computed fields are NOT populated
        # that way and the NOT NULL constraint will fail.
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
                'is_reward_line': True,
            })],
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })
        cls.order_line = cls.pos_order.lines[0]

    # -----------------------------------------------------------------------
    # Field Tests
    # -----------------------------------------------------------------------

    def test_points_remaining_field_exists(self):
        """points_remaining field should exist on pos.order.line."""
        self.assertIn(
            'points_remaining',
            self.order_line._fields,
            "Field 'points_remaining' must exist on pos.order.line."
        )

    def test_points_remaining_default_zero(self):
        """points_remaining should default to 0.0."""
        self.assertEqual(
            self.order_line.points_remaining,
            0.0,
            "points_remaining should default to 0.0."
        )

    # -----------------------------------------------------------------------
    # remaining_points() Method Tests
    # -----------------------------------------------------------------------

    def test_remaining_points_sets_value(self):
        """remaining_points() should write the balance onto the reward line."""
        self.env['pos.order.line'].remaining_points(
            [150.0], [self.pos_order.access_token])
        self.assertEqual(
            self.order_line.points_remaining,
            150.0,
            "remaining_points() should set points_remaining to the given balance."
        )

    def test_remaining_points_updates_existing_value(self):
        """Calling remaining_points() twice should update to the latest value."""
        self.env['pos.order.line'].remaining_points(
            [50.0], [self.pos_order.access_token])
        self.env['pos.order.line'].remaining_points(
            [200.0], [self.pos_order.access_token])
        self.assertEqual(
            self.order_line.points_remaining,
            200.0,
            "remaining_points() should overwrite with the latest balance."
        )

    def test_remaining_points_no_match_token(self):
        """remaining_points() with a wrong token should not raise, just skip."""
        try:
            self.env['pos.order.line'].remaining_points(
                [99.0], ['invalid-token-xyz'])
        except Exception as e:
            self.fail(
                f"remaining_points() raised unexpectedly for bad token: {e}")

    def test_reward_line_flag(self):
        """The order line created with is_reward_line=True should reflect that."""
        self.assertTrue(
            self.order_line.is_reward_line,
            "Order line should be flagged as a reward line."
        )