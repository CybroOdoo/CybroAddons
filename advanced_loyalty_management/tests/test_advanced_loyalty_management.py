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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAdvancedLoyaltyManagement(TransactionCase):
    """Complete test suite for advanced_loyalty_management module covering:
    - loyalty.program: field definitions, _load_pos_data_fields, convert_loyalty logic
    - loyalty.reward: redemption reward type, fields, defaults, description computation, _load_pos_data_fields
    - pos.order.line: points_remaining field, remaining_points logic and loyalty history creation
    - res.partner: pos_order_ids field, _load_pos_data_fields, action_view_redemption_history, check_redemption
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Partner setup
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Customer Alpha',
            'email': 'alpha@example.com',
            'company_id': cls.company.id,
        })
        cls.partner_b = cls.env['res.partner'].create({
            'name': 'Customer Beta',
            'email': 'beta@example.com',
            'company_id': cls.company.id,
        })

        # Loyalty Program setup
        cls.loyalty_program = cls.env['loyalty.program'].create({
            'name': 'Test Advanced Loyalty Program',
            'program_type': 'loyalty',
            'point_rate': 2,
            'change_rate': 1.0,
            'applies_on': 'both',
            'company_id': cls.company.id,
        })

        # Product setup
        cls.product = cls.env['product.product'].create({
            'name': 'Test POS Merchandise',
            'list_price': 25.0,
            'type': 'consu',
            'company_id': cls.company.id,
        })
        cls.reward_product = cls.env['product.product'].create({
            'name': 'Test Reward Discount Line Product',
            'list_price': 0.0,
            'type': 'service',
            'company_id': cls.company.id,
        })

        # Loyalty Reward: Redemption type
        cls.reward_redemption = cls.env['loyalty.reward'].create({
            'program_id': cls.loyalty_program.id,
            'reward_type': 'redemption',
            'discount_line_product_id': cls.reward_product.id,
            'redemption_point': 1,
            'redemption_amount': 2.5,
            'max_redemption_type': 'amount',
            'max_redemption_amount': 20.0,
            'redemption_frequency': 3,
            'redemption_frequency_unit': 'week',
            'redemption_eligibility': 150.0,
        })

        # Loyalty Reward: Discount type (to test compute description fallback)
        cls.reward_discount = cls.env['loyalty.reward'].create({
            'program_id': cls.loyalty_program.id,
            'reward_type': 'discount',
            'discount': 10.0,
            'discount_mode': 'percent',
            'discount_line_product_id': cls.reward_product.id,
        })

        # POS Configuration & Session setup
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Store',
            'company_id': cls.company.id,
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })

    # =========================================================================
    # 1. Tests for loyalty.program
    # =========================================================================

    def test_loyalty_program_defaults(self):
        """Test default values of point_rate, change_rate, and currency_id."""
        program = self.env['loyalty.program'].create({
            'name': 'Default Loyalty Test',
            'program_type': 'loyalty',
        })
        self.assertEqual(program.point_rate, 1, "Default point_rate should be 1.")
        self.assertEqual(program.change_rate, 1.0, "Default change_rate should be 1.0.")
        self.assertEqual(
            program.currency_id,
            self.env.company.currency_id,
            "Default currency_id should match company currency."
        )

    def test_loyalty_program_load_pos_data_fields(self):
        """Verify _load_pos_data_fields includes point_rate and change_rate."""
        fields = self.env['loyalty.program']._load_pos_data_fields(self.pos_config.id)
        self.assertIn('point_rate', fields, "'point_rate' must be loaded for POS.")
        self.assertIn('change_rate', fields, "'change_rate' must be loaded for POS.")

    def test_convert_loyalty_new_card(self):
        """Test converting change to points when customer does not have an existing card (cid < 0)."""
        change_points = 50.0
        # Call convert_loyalty with negative coupon id (e.g. [-1]) indicating new card
        self.env['loyalty.program'].convert_loyalty(
            [self.loyalty_program.id],
            [-self.loyalty_program.id],
            [change_points],
            [self.partner_a.id]
        )

        card = self.env['loyalty.card'].search([
            ('partner_id', '=', self.partner_a.id),
            ('program_id', '=', self.loyalty_program.id),
        ], limit=1)
        self.assertTrue(card, "A new loyalty card should be created for the partner.")

        history = self.env['loyalty.history'].search([('card_id', '=', card.id)], order='id desc', limit=1)
        self.assertTrue(history, "A loyalty history entry should be recorded.")
        self.assertEqual(history.description, 'Change converted to loyalty points')
        self.assertEqual(history.issued, change_points)
        self.assertEqual(history.used, 0.0)

    def test_convert_loyalty_existing_card(self):
        """Test converting change to points on an existing loyalty card (cid >= 0)."""
        card = self.env['loyalty.card'].create({
            'program_id': self.loyalty_program.id,
            'partner_id': self.partner_b.id,
            'points': 20.0,
        })
        initial_history_count = self.env['loyalty.history'].search_count([('card_id', '=', card.id)])

        add_points = 35.0
        self.env['loyalty.program'].convert_loyalty(
            [self.loyalty_program.id],
            [card.id],
            [add_points],
            [self.partner_b.id]
        )

        new_history_count = self.env['loyalty.history'].search_count([('card_id', '=', card.id)])
        self.assertEqual(new_history_count, initial_history_count + 1)

        history = self.env['loyalty.history'].search([('card_id', '=', card.id)], order='id desc', limit=1)
        self.assertEqual(history.description, 'Change converted to loyalty points')
        self.assertEqual(history.issued, add_points)
        self.assertEqual(history.used, 0.0)

    def test_convert_loyalty_existing_card_negative_points(self):
        """Test convert_loyalty when existing card points are negative."""
        card = self.env['loyalty.card'].create({
            'program_id': self.loyalty_program.id,
            'partner_id': self.partner_b.id,
        })
        # Simulate negative points
        card.points = -15.0

        self.env['loyalty.program'].convert_loyalty(
            [self.loyalty_program.id],
            [card.id],
            [40.0],
            [self.partner_b.id]
        )

        history = self.env['loyalty.history'].search([('card_id', '=', card.id)], order='id desc', limit=1)
        self.assertEqual(history.issued, 40.0)

    # =========================================================================
    # 2. Tests for loyalty.reward
    # =========================================================================

    def test_loyalty_reward_redemption_fields_and_defaults(self):
        """Test custom fields on loyalty.reward for redemption reward type."""
        reward = self.reward_redemption
        self.assertEqual(reward.reward_type, 'redemption')
        self.assertEqual(reward.redemption_point, 1)
        self.assertEqual(reward.redemption_amount, 2.5)
        self.assertEqual(reward.max_redemption_type, 'amount')
        self.assertEqual(reward.max_redemption_amount, 20.0)
        self.assertEqual(reward.redemption_frequency, 3)
        self.assertEqual(reward.redemption_frequency_unit, 'week')
        self.assertEqual(reward.redemption_eligibility, 150.0)

    def test_loyalty_reward_compute_description(self):
        """Test _compute_description sets 'Redemption' for redemption rewards."""
        self.reward_redemption._compute_description()
        self.assertEqual(self.reward_redemption.description, 'Redemption')

        # Test non-redemption reward does not get forced to 'Redemption'
        self.reward_discount._compute_description()
        self.assertNotEqual(self.reward_discount.description, 'Redemption')

    def test_loyalty_reward_load_pos_data_fields(self):
        """Verify _load_pos_data_fields includes all custom redemption fields."""
        fields = self.env['loyalty.reward']._load_pos_data_fields(self.pos_config.id)
        expected_fields = [
            'redemption_point',
            'redemption_amount',
            'max_redemption_amount',
            'redemption_frequency',
            'redemption_frequency_unit',
            'redemption_eligibility',
            'max_redemption_type'
        ]
        for field in expected_fields:
            self.assertIn(field, fields, f"Field '{field}' should be in loaded POS fields.")

    # =========================================================================
    # 3. Tests for pos.order.line
    # =========================================================================

    def test_pos_order_line_remaining_points_invalid_token(self):
        """Test remaining_points returns gracefully when POS order uuid is not found."""
        # Should return without raising any exception
        result = self.env['pos.order.line'].remaining_points([50.0], ['invalid-uuid-token'])
        self.assertIsNone(result)

    def test_pos_order_line_remaining_points_with_reward_lines(self):
        """Test remaining_points updates points_remaining on reward lines and creates history."""
        # Create loyalty card for partner
        card = self.env['loyalty.card'].create({
            'program_id': self.loyalty_program.id,
            'partner_id': self.partner_a.id,
            'points': 100.0,
        })

        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'partner_id': self.partner_a.id,
            'uuid': 'test-uuid-order-with-reward',
            'lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'qty': 1,
                    'price_unit': 25.0,
                    'price_subtotal': 25.0,
                    'price_subtotal_incl': 25.0,
                }),
                (0, 0, {
                    'product_id': self.reward_product.id,
                    'qty': 1,
                    'price_unit': -5.0,
                    'price_subtotal': -5.0,
                    'price_subtotal_incl': -5.0,
                    'is_reward_line': True,
                    'reward_id': self.reward_redemption.id,
                    'points_cost': 15.0,
                }),
            ],
            'amount_total': 20.0,
            'amount_tax': 0.0,
            'amount_paid': 20.0,
            'amount_return': 0.0,
        })

        balance_to_set = 85.0
        self.env['pos.order.line'].remaining_points([balance_to_set], [order.uuid])

        reward_line = order.lines.filtered('is_reward_line')
        self.assertEqual(reward_line.points_remaining, balance_to_set)

        history = self.env['loyalty.history'].search([
            ('card_id', '=', card.id),
            ('order_id', '=', order.id),
        ], limit=1)
        self.assertTrue(history, "Loyalty history entry should be created for points redeemed.")
        self.assertEqual(history.used, 15.0)
        self.assertEqual(history.issued, 0.0)
        self.assertEqual(history.order_model, 'pos.order')
        self.assertIn(order.name, history.description)

    def test_pos_order_line_remaining_points_without_reward_lines(self):
        """Test remaining_points when order has no reward lines (falls back to order.lines)."""
        card = self.env['loyalty.card'].create({
            'program_id': self.loyalty_program.id,
            'partner_id': self.partner_a.id,
            'points': 50.0,
        })

        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'partner_id': self.partner_a.id,
            'uuid': 'test-uuid-order-no-reward',
            'lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'qty': 2,
                    'price_unit': 25.0,
                    'price_subtotal': 50.0,
                    'price_subtotal_incl': 50.0,
                    'is_reward_line': False,
                    'points_cost': 0.0,
                }),
            ],
            'amount_total': 50.0,
            'amount_tax': 0.0,
            'amount_paid': 50.0,
            'amount_return': 0.0,
        })

        balance_to_set = 50.0
        self.env['pos.order.line'].remaining_points([balance_to_set], [order.uuid])

        self.assertEqual(order.lines[0].points_remaining, balance_to_set)

    def test_pos_order_line_remaining_points_partner_without_card(self):
        """Test remaining_points when partner does not have a loyalty card."""
        partner_no_card = self.env['res.partner'].create({'name': 'Customer No Card'})

        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'partner_id': partner_no_card.id,
            'uuid': 'test-uuid-order-partner-no-card',
            'lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'qty': 1,
                    'price_unit': 25.0,
                    'price_subtotal': 25.0,
                    'price_subtotal_incl': 25.0,
                }),
            ],
            'amount_total': 25.0,
            'amount_tax': 0.0,
            'amount_paid': 25.0,
            'amount_return': 0.0,
        })

        self.env['pos.order.line'].remaining_points([10.0], [order.uuid])
        self.assertEqual(order.lines[0].points_remaining, 10.0)

    # =========================================================================
    # 4. Tests for res.partner
    # =========================================================================

    def test_res_partner_load_pos_data_fields(self):
        """Verify _load_pos_data_fields includes pos_order_ids for res.partner."""
        fields = self.env['res.partner']._load_pos_data_fields(self.pos_config.id)
        self.assertIn('pos_order_ids', fields, "'pos_order_ids' should be in loaded POS fields.")

    def test_res_partner_action_view_redemption_history(self):
        """Test action_view_redemption_history returns proper window action."""
        action = self.partner_a.action_view_redemption_history()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'loyalty.history')
        self.assertEqual(action.get('domain'), [('card_id.partner_id', '=', self.partner_a.id)])
        self.assertEqual(action.get('context'), "{'create': False}")

    def test_res_partner_check_redemption_with_redemption_orders(self):
        """Test check_redemption returns order IDs and dates for partner with redemption orders."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'partner_id': self.partner_a.id,
            'uuid': 'test-uuid-check-redemption-partner',
            'lines': [
                (0, 0, {
                    'product_id': self.reward_product.id,
                    'qty': 1,
                    'price_unit': -10.0,
                    'price_subtotal': -10.0,
                    'price_subtotal_incl': -10.0,
                    'is_reward_line': True,
                    'reward_id': self.reward_redemption.id,
                }),
            ],
            'amount_total': 0.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })

        data, dates = self.env['res.partner'].check_redemption([self.partner_a.id])
        self.assertIn(order.id, data, "Order ID should be present in check_redemption results.")
        self.assertTrue(len(dates) > 0, "Dates list should contain creation date.")

    def test_res_partner_check_redemption_without_redemptions(self):
        """Test check_redemption returns empty lists when partner has no redemption orders."""
        data, dates = self.env['res.partner'].check_redemption([self.partner_b.id])
        self.assertEqual(data, [])
        self.assertEqual(dates, [])
