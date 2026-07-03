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

class TestResPartner(TransactionCase):
    """Test cases for ResPartner extensions in advanced_loyalty_management."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Partner Redemption Test',
        })

        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Partner POS',
            })

        cls.product = cls.env['product.product'].search(
            [('available_in_pos', '=', True)], limit=1)
        if not cls.product:
            cls.product = cls.env['product.product'].create({
                'name': 'Partner Test Product',
                'available_in_pos': True,
                'list_price': 100.0,
                'taxes_id': [],
            })

        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })

        # Create POS order with lines embedded — price_subtotal is a NOT NULL
        # DB column; supplying it in the lines tuple avoids the constraint
        # violation that occurs when creating pos.order.line directly.
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

        cls.loyalty_program = cls.env['loyalty.program'].search(
            [('program_type', '=', 'loyalty')], limit=1)
        if not cls.loyalty_program:
            cls.loyalty_program = cls.env['loyalty.program'].create({
                'name': 'Partner Loyalty Program',
                'program_type': 'loyalty',
            })

        cls.loyalty_card = cls.env['loyalty.card'].create({
            'program_id': cls.loyalty_program.id,
            'partner_id': cls.partner.id,
            'points': 200.0,
        })

    # -----------------------------------------------------------------------
    # Field Tests
    # -----------------------------------------------------------------------

    def test_pos_order_ids_field_exists(self):
        """pos_order_ids One2many field should exist on res.partner."""
        self.assertIn(
            'pos_order_ids',
            self.partner._fields,
            "Field 'pos_order_ids' must exist on res.partner."
        )

    def test_pos_order_ids_contains_order(self):
        """Partner's pos_order_ids should include the created POS order."""
        self.assertIn(
            self.pos_order,
            self.partner.pos_order_ids,
            "Partner's pos_order_ids should include the test order."
        )

    # -----------------------------------------------------------------------
    # action_view_redemption_history() Tests
    # -----------------------------------------------------------------------

    def test_action_view_redemption_history_returns_action(self):
        """action_view_redemption_history() should return a window action dict."""
        action = self.partner.action_view_redemption_history()
        self.assertEqual(
            action.get('type'),
            'ir.actions.act_window',
            "Should return an ir.actions.act_window action."
        )

    def test_action_view_redemption_history_model(self):
        """The action should target pos.order.line."""
        action = self.partner.action_view_redemption_history()
        self.assertEqual(
            action.get('res_model'),
            'pos.order.line',
            "Action res_model should be 'pos.order.line'."
        )

    def test_action_view_redemption_history_name(self):
        """The action name should be 'Redemption History'."""
        action = self.partner.action_view_redemption_history()
        self.assertEqual(
            action.get('name'),
            'Redemption History',
            "Action name should be 'Redemption History'."
        )

    # -----------------------------------------------------------------------
    # check_redemption() Tests
    # -----------------------------------------------------------------------

    def test_check_redemption_returns_two_lists(self):
        """check_redemption() should return a tuple of two lists."""
        result = self.env['res.partner'].check_redemption([self.partner.id])
        self.assertIsInstance(result, tuple, "Should return a tuple.")
        self.assertEqual(len(result), 2, "Tuple should have exactly 2 elements.")

    def test_check_redemption_order_ids_list(self):
        """First element of check_redemption() should be a list of order IDs."""
        order_ids, dates = self.env['res.partner'].check_redemption(
            [self.partner.id])
        self.assertIsInstance(order_ids, list,
                              "First return value should be a list.")

    def test_check_redemption_date_list(self):
        """Second element of check_redemption() should be a list of dates."""
        order_ids, dates = self.env['res.partner'].check_redemption(
            [self.partner.id])
        self.assertIsInstance(dates, list,
                              "Second return value should be a list.")

    def test_check_redemption_contains_reward_order(self):
        """check_redemption() should include the order with a reward line."""
        order_ids, dates = self.env['res.partner'].check_redemption(
            [self.partner.id])
        self.assertIn(
            self.pos_order.id,
            order_ids,
            "check_redemption() should return the order ID that has a reward line."
        )