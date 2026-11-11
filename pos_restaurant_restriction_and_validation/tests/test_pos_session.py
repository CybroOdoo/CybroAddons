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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosSession(TransactionCase):
    """Unit tests for pos.session close validation."""

    @classmethod
    def setUpClass(cls):
        """Set up POS session test environment."""
        super().setUpClass()
        cls.pos_manager_group = cls.env.ref('point_of_sale.group_pos_manager')
        cls.pos_user_group = cls.env.ref('point_of_sale.group_pos_user')

        cls.manager_user = cls.env['res.users'].create({
            'name': 'Session Test Manager',
            'login': 'session_test_mgr',
            'email': 'session_mgr@test.com',
            'group_ids': [(6, 0, [cls.pos_manager_group.id, cls.pos_user_group.id])],
            'pos_security_pin': '1234',
        })
        cls.cashier_user = cls.env['res.users'].create({
            'name': 'Session Test Cashier',
            'login': 'session_test_cashier',
            'email': 'session_cashier@test.com',
            'group_ids': [(6, 0, [cls.pos_user_group.id])],
        })

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Session Restaurant Store',
            'pos_restaurant_restriction': True,
            'pos_session_close': True,
        })
        cls.pos_session = cls.env['pos.session'].create({
            'name': 'Test Session',
            'config_id': cls.pos_config.id,
            'state': 'closed',
        })

    def test_close_session_from_ui_blocks_unauthorized_cashier(self):
        """Verify closing session without manager approval raises UserError."""
        with self.assertRaises(UserError):
            self.pos_session.with_user(self.cashier_user).close_session_from_ui()

    def test_close_session_from_ui_allows_manager(self):
        """Verify closing session succeeds when executed by a manager."""
        res = self.pos_session.with_user(self.manager_user).close_session_from_ui()
        self.assertIsInstance(res, dict)

    def test_close_session_from_ui_allows_with_approval_log(self):
        """Verify closing session succeeds when manager approval log exists with session reference."""
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'session_close',
            'order_ref': self.pos_session.name,
            'approved_by': self.manager_user.id,
        })
        res = self.pos_session.with_user(self.cashier_user).close_session_from_ui()
        self.assertIsInstance(res, dict)

    def test_close_session_from_ui_rejects_wrong_or_missing_session_reference(self):
        """Verify session close fails if approval is for a different session or lacks session reference."""
        # Approval without order_ref
        log_no_ref = self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'session_close',
            'order_ref': False,
            'approved_by': self.manager_user.id,
        })
        with self.assertRaises(UserError):
            self.pos_session.with_user(self.cashier_user).close_session_from_ui()
        log_no_ref.sudo().unlink()

        # Approval with different session reference
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'session_close',
            'order_ref': 'Other Session Name',
            'approved_by': self.manager_user.id,
        })
        with self.assertRaises(UserError):
            self.pos_session.with_user(self.cashier_user).close_session_from_ui()

    def test_close_session_from_ui_consumes_approval(self):
        """Verify manager approval is consumed upon closing session and cannot be reused."""
        log = self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'session_close',
            'order_ref': self.pos_session.name,
            'approved_by': self.manager_user.id,
        })
        self.assertFalse(log.is_consumed)
        self.pos_session.with_user(self.cashier_user).close_session_from_ui()
        self.assertTrue(log.is_consumed)

        # Attempting again without new approval raises UserError
        with self.assertRaises(UserError):
            self.pos_session.with_user(self.cashier_user).close_session_from_ui()

    def test_close_session_from_ui_rejects_different_cashier_approval(self):
        """Verify an approval created for Cashier A cannot be used by Cashier B."""
        other_cashier = self.env['res.users'].create({
            'name': 'Other Cashier',
            'login': 'other_cashier_session',
            'email': 'other_cashier@test.com',
            'group_ids': [(6, 0, [self.pos_user_group.id])],
        })
        self.env['pos.action.log'].sudo().create({
            'user_id': other_cashier.id,
            'cashier_name': other_cashier.name,
            'action_type': 'session_close',
            'order_ref': self.pos_session.name,
            'approved_by': self.manager_user.id,
        })
        with self.assertRaises(UserError):
            self.pos_session.with_user(self.cashier_user).close_session_from_ui()

    def test_close_session_from_ui_restriction_disabled(self):
        """Verify closing session proceeds when restriction is disabled."""
        self.pos_config.write({'pos_session_close': False})
        res = self.pos_session.with_user(self.cashier_user).close_session_from_ui()
        self.assertIsInstance(res, dict)

        # Test with master toggle disabled
        self.pos_config.write({
            'pos_session_close': True,
            'pos_restaurant_restriction': False,
        })
        res2 = self.pos_session.with_user(self.cashier_user).close_session_from_ui()
        self.assertIsInstance(res2, dict)

    def test_close_session_from_ui_allows_with_context_bypass(self):
        """Verify closing session succeeds with pos_restriction_approved in context."""
        res = self.pos_session.with_user(self.cashier_user).with_context(
            pos_restriction_approved=True
        ).close_session_from_ui()
        self.assertIsInstance(res, dict)

    def test_close_session_from_ui_with_custom_payment_closing_dict(self):
        """Verify passing payment_method_closing positionally and by keyword is supported."""
        self.pos_config.write({'pos_session_close': True})
        dummy_closing = {'1': 100.0}

        # Positional argument with valid approval log
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'session_close',
            'order_ref': self.pos_session.name,
            'approved_by': self.manager_user.id,
        })
        res = self.pos_session.with_user(self.cashier_user).close_session_from_ui(dummy_closing)
        self.assertIsInstance(res, dict)

        # Keyword argument when restriction disabled
        self.pos_config.write({'pos_session_close': False})
        res_kw = self.pos_session.with_user(self.cashier_user).close_session_from_ui(
            payment_method_closing=dummy_closing
        )
        self.assertIsInstance(res_kw, dict)

