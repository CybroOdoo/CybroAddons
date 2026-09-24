# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
###############################################################################

from odoo.tests import common
from odoo.exceptions import ValidationError
from odoo.fields import Command


class TestEwalletCreditLimit(common.TransactionCase):
    """Test suite to verify the credit limit functionality for e-wallets."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a test customer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        # Create a test product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 50.0,
            'sale_ok': True,
        })

        # Create an e-wallet loyalty program
        cls.ewallet_program = cls.env['loyalty.program'].create({
            'name': 'E-Wallet Test Program',
            'program_type': 'ewallet',
            'trigger': 'auto',
            'applies_on': 'future',
            'reward_ids': [Command.create({
                'reward_type': 'discount',
                'discount_mode': 'per_point',
                'discount': 1,
            })],
        })

        # Create an e-wallet card with 100 points
        cls.ewallet_card = cls.env['loyalty.card'].create({
            'program_id': cls.ewallet_program.id,
            'partner_id': cls.partner.id,
            'points': 100.0,
        })

    def test_01_loyalty_card_credit_limit_computations(self):
        """Test loyalty card credit limit computations and validation constraints."""
        # By default, set_limit is False. balance_limit_amount should be 0.0.
        self.assertFalse(self.ewallet_card.set_limit)
        self.assertEqual(self.ewallet_card.balance_limit_amount, 0.0)

        # Enable set_limit and set limit to 80.0
        self.ewallet_card.write({
            'set_limit': True,
            'limit': 80.0,
        })
        self.assertEqual(self.ewallet_card.balance_limit_amount, 80.0)

        # Update used_limit, verify balance_limit_amount decreases
        self.ewallet_card.write({
            'used_limit': 30.0,
        })
        self.assertEqual(self.ewallet_card.balance_limit_amount, 50.0)

        # Try to set a limit that exceeds points (balance_limit_amount > points)
        # points = 100.0, used_limit = 30.0.
        # If we set limit = 150.0, balance_limit_amount becomes 150.0 - 30.0 = 120.0.
        # Since 120.0 > 100.0, it should raise ValidationError.
        with self.assertRaises(ValidationError):
            self.ewallet_card.write({
                'limit': 150.0,
            })

    def test_02_sale_order_get_real_points(self):
        """Test _get_real_points_for_coupon under different credit limit scenarios."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

        # Scenario A: set_limit is False. Real points should equal the e-wallet points.
        self.ewallet_card.write({
            'set_limit': False,
            'limit': 0.0,
            'used_limit': 0.0,
        })
        points = order._get_real_points_for_coupon(self.ewallet_card)
        self.assertEqual(points, 100.0)

        # Scenario B: set_limit is True, limit is 80.0, used_limit is 0.0 (points=100.0)
        # Points returned should be min(80.0, 100.0) = 80.0
        self.ewallet_card.write({
            'set_limit': True,
            'limit': 80.0,
            'used_limit': 0.0,
        })
        points = order._get_real_points_for_coupon(self.ewallet_card)
        self.assertEqual(points, 80.0)

        # Scenario C: set_limit is True, limit is 80.0, used_limit is 80.0 (balance_limit_amount = 0.0)
        # Should raise ValidationError since balance_limit_amount <= 0.0
        self.ewallet_card.write({
            'used_limit': 80.0,
        })
        with self.assertRaises(ValidationError):
            order._get_real_points_for_coupon(self.ewallet_card)

    def test_03_sale_order_confirm_cancel(self):
        """Test that confirming and cancelling a Sale Order updates the e-wallet's used_limit."""
        self.ewallet_card.write({
            'set_limit': True,
            'limit': 80.0,
            'used_limit': 10.0,
        })

        # Create a sale order with an e-wallet line manually to isolate testing confirm/cancel hooks
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 50.0,
                }),
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': -25.0,
                    'coupon_id': self.ewallet_card.id,
                    'points_cost': 25.0,
                })
            ]
        })

        # Before confirm, used_limit should be 10.0
        self.assertEqual(self.ewallet_card.used_limit, 10.0)

        # Confirm the sale order
        order.action_confirm()

        # After confirm, used_limit should be updated (10.0 + 25.0 = 35.0)
        self.assertEqual(self.ewallet_card.used_limit, 35.0)

        # Cancel the sale order
        order._action_cancel()

        # After cancel, used_limit should be restored (35.0 - 25.0 = 10.0)
        self.assertEqual(self.ewallet_card.used_limit, 10.0)

    def test_04_pos_order_set_remaining_balance(self):
        """Test set_remaining_balance updates loyalty card used_limit from POS order line data."""
        self.ewallet_card.write({
            'used_limit': 15.0,
        })

        data = [
            {
                'coupon_id': self.ewallet_card.id,
                'point_cost': 20.0,
            },
            {
                'coupon_id': self.ewallet_card.id,
                'point_cost': 10.0,
            },
            {
                # Line without coupon_id should be ignored
                'point_cost': 50.0,
            }
        ]

        res = self.env['pos.order'].set_remaining_balance(data)
        self.assertTrue(res)
        # used_limit should be 15.0 + 20.0 + 10.0 = 45.0
        self.assertEqual(self.ewallet_card.used_limit, 45.0)

    def test_05_pos_session_loader(self):
        """Test POS Session loader methods for loyalty card credit limit fields."""
        pos_session = self.env['pos.session']

        # 1. Test _pos_ui_models_to_load loads loyalty.card
        models_to_load = pos_session._pos_ui_models_to_load()
        self.assertIn('loyalty.card', models_to_load)

        # 2. Test _loader_params_loyalty_card specifies fields
        loader_params = pos_session._loader_params_loyalty_card()
        self.assertIn('search_params', loader_params)
        self.assertIn('fields', loader_params['search_params'])
        fields = loader_params['search_params']['fields']
        for field in ['id', 'points', 'set_limit', 'balance_limit_amount']:
            self.assertIn(field, fields)

        # 3. Test _get_pos_ui_loyalty_card fetches records correctly
        params = {
            'search_params': {
                'domain': [('id', '=', self.ewallet_card.id)],
                'fields': ['id', 'points', 'set_limit', 'balance_limit_amount']
            }
        }
        res = pos_session._get_pos_ui_loyalty_card(params)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['id'], self.ewallet_card.id)
        self.assertEqual(res[0]['points'], self.ewallet_card.points)
