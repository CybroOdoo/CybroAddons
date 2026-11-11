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
from datetime import timedelta
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosConfig(TransactionCase):
    """Unit tests for pos.config approval flows and restriction checks."""

    @classmethod
    def setUpClass(cls):
        """Set up POS config, manager, and cashier users."""
        super().setUpClass()
        cls.pos_manager_group = cls.env.ref('point_of_sale.group_pos_manager')
        cls.pos_user_group = cls.env.ref('point_of_sale.group_pos_user')

        cls.manager_user = cls.env['res.users'].create({
            'name': 'Valid POS Manager',
            'login': 'valid_pos_manager_cfg',
            'email': 'manager_cfg@test.com',
            'group_ids': [(6, 0, [cls.pos_manager_group.id, cls.pos_user_group.id])],
            'pos_security_pin': '7788',
        })

        cls.manager_without_pin = cls.env['res.users'].create({
            'name': 'Manager Without Pin',
            'login': 'manager_without_pin_cfg',
            'email': 'nopin_cfg@test.com',
            'group_ids': [(6, 0, [cls.pos_manager_group.id, cls.pos_user_group.id])],
            'pos_security_pin': False,
        })

        cls.cashier_user = cls.env['res.users'].create({
            'name': 'Standard Cashier',
            'login': 'standard_cashier_cfg',
            'email': 'cashier_cfg@test.com',
            'group_ids': [(6, 0, [cls.pos_user_group.id])],
            'pos_security_pin': '9999',
        })

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Restriction Config Store',
            'pos_restaurant_restriction': True,
            'pos_orderline_quantity_update': True,
            'pos_orderline_delete': True,
            'pos_order_delete': True,
            'pos_session_close': True,
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Config Test Product',
            'list_price': 50.0,
            'available_in_pos': True,
        })

    def test_load_pos_data_read(self):
        """Verify _load_pos_data_read populates custom restriction settings."""
        records = self.pos_config
        res = self.env['pos.config']._load_pos_data_read(records, self.pos_config)
        self.assertEqual(len(res), 1)
        self.assertTrue(res[0]['pos_restaurant_restriction'])
        self.assertTrue(res[0]['pos_orderline_quantity_update'])
        self.assertTrue(res[0]['pos_orderline_delete'])
        self.assertTrue(res[0]['pos_order_delete'])
        self.assertTrue(res[0]['pos_session_close'])

    def test_get_managers_for_approval(self):
        """Verify get_managers_for_approval filters users correctly when called by cashier."""
        managers = self.pos_config.with_user(self.cashier_user).get_managers_for_approval()
        manager_ids = [m['id'] for m in managers]
        self.assertIn(self.manager_user.id, manager_ids)
        self.assertNotIn(self.manager_without_pin.id, manager_ids)
        self.assertNotIn(self.cashier_user.id, manager_ids)

    def test_get_managers_for_approval_as_cashier(self):
        """Verify cashier user can call get_managers_for_approval without AccessError."""
        managers = self.pos_config.with_user(self.cashier_user).get_managers_for_approval()
        manager_ids = [m['id'] for m in managers]
        self.assertIn(self.manager_user.id, manager_ids)
        self.assertNotIn(self.cashier_user.id, manager_ids)
        self.assertNotIn(self.manager_without_pin.id, manager_ids)

    def test_validate_manager_pin_as_cashier(self):
        """Verify cashier user can call validate_manager_pin_for_restriction without AccessError."""
        res = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
            config_id=self.pos_config.id,
            manager_id=self.manager_user.id,
            pin='7788',
            action_type='orderline_delete',
        )
        self.assertTrue(res.get('approved'))

    def test_validate_manager_pin_anti_spoofing_as_cashier(self):
        """Verify that a cashier cannot spoof cashier_user_id or cashier_name in the audit log."""
        res = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
            config_id=self.pos_config.id,
            manager_id=self.manager_user.id,
            pin='7788',
            action_type='orderline_delete',
            order_ref='ORDER/SPOOF/TEST',
            cashier_user_id=self.manager_user.id,
            cashier_name='Fake Manager',
        )
        self.assertTrue(res.get('approved'))
        log = self.env['pos.action.log'].search([
            ('order_ref', '=', 'ORDER/SPOOF/TEST'),
            ('action_type', '=', 'orderline_delete'),
        ], limit=1)
        self.assertTrue(log)
        # Forced to actual authenticated cashier user
        self.assertEqual(log.user_id, self.cashier_user)
        self.assertEqual(log.cashier_name, self.cashier_user.name)

    def test_validate_manager_pin_rate_limiting_and_lockout(self):
        """Verify failed PIN attempts lock out only the caller, not the manager."""
        other_cashier = self.env['res.users'].create({
            'name': 'Other Rate Limit Cashier',
            'login': 'other_rate_limit_cashier',
            'email': 'other_rate@test.com',
            'group_ids': [(6, 0, [self.pos_user_group.id])],
        })
        self.manager_user.sudo().write({'pos_pin_failed_attempts': 0, 'pos_pin_lockout_until': False})
        self.cashier_user.sudo().write({'pos_pin_failed_attempts': 0, 'pos_pin_lockout_until': False})

        # 4 failed attempts should not lock out
        for _ in range(4):
            res = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
                self.pos_config.id, self.manager_user.id, '0000', 'orderline_delete'
            )
            self.assertFalse(res.get('approved'))
            self.assertFalse(res.get('locked'))

        # 5th failed attempt triggers lockout on the caller
        res_5th = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, '0000', 'orderline_delete'
        )
        self.assertFalse(res_5th.get('approved'))

        # 6th attempt by same caller (even with valid PIN) is rejected due to caller lockout
        res_6th = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, '7788', 'orderline_delete'
        )
        self.assertFalse(res_6th.get('approved'))
        self.assertTrue(res_6th.get('locked'))

        # Manager is NOT locked out for other cashiers
        self.assertEqual(self.manager_user.pos_pin_failed_attempts, 0)
        self.assertFalse(self.manager_user.pos_pin_lockout_until)
        res_other = self.pos_config.with_user(other_cashier).validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, '7788', 'orderline_delete'
        )
        self.assertTrue(res_other.get('approved'))

        # Clean up lockout
        self.cashier_user.sudo().write({'pos_pin_failed_attempts': 0, 'pos_pin_lockout_until': False})

    def test_validate_manager_pin_empty_or_falsy(self):
        """Verify empty or falsy pin is rejected."""
        res_false = self.pos_config.validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, False, 'orderline_delete'
        )
        self.assertFalse(res_false['approved'])

        res_empty = self.pos_config.validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, "   ", 'orderline_delete'
        )
        self.assertFalse(res_empty['approved'])

    def test_validate_manager_pin_wrong_or_invalid_user(self):
        """Verify non-managers and incorrect PINs are rejected."""
        # Non-manager user with a PIN
        res_non_mgr = self.pos_config.validate_manager_pin_for_restriction(
            self.pos_config.id, self.cashier_user.id, '9999', 'orderline_delete'
        )
        self.assertFalse(res_non_mgr['approved'])

        # Valid manager with wrong PIN
        res_wrong_pin = self.pos_config.validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, '0000', 'orderline_delete'
        )
        self.assertFalse(res_wrong_pin['approved'])

    def test_validate_manager_pin_success_and_log_creation(self):
        """Verify correct PIN returns approved=True and creates an audit log."""
        res = self.pos_config.validate_manager_pin_for_restriction(
            config_id=self.pos_config.id,
            manager_id=self.manager_user.id,
            pin='7788',
            action_type='orderline_quantity_update',
            product_id=self.product.id,
            old_qty=3.0,
            new_qty=1.0,
            order_ref='ORDER/REF/100',
            cashier_user_id=self.cashier_user.id,
            cashier_name='Frontend Cashier One',
        )
        self.assertTrue(res.get('approved'))

        log = self.env['pos.action.log'].search([
            ('order_ref', '=', 'ORDER/REF/100'),
            ('action_type', '=', 'orderline_quantity_update'),
        ], limit=1)
        self.assertTrue(log)
        self.assertEqual(log.user_id, self.cashier_user)
        self.assertEqual(log.cashier_name, 'Frontend Cashier One')
        self.assertEqual(log.approved_by, self.manager_user)
        self.assertEqual(log.product_id, self.product)
        self.assertEqual(log.old_qty, 3.0)
        self.assertEqual(log.new_qty, 1.0)
        self.assertFalse(log.is_consumed)

    def test_is_restriction_authorized(self):
        """Verify is_restriction_authorized under various permissions, log states, and consumption."""
        # Manager user is always authorized
        pos_config_as_manager = self.pos_config.with_user(self.manager_user)
        self.assertTrue(pos_config_as_manager.is_restriction_authorized('orderline_delete'))

        # Superuser is always authorized
        pos_config_as_su = self.pos_config.with_env(self.env(su=True))
        self.assertTrue(pos_config_as_su.is_restriction_authorized('orderline_delete'))

        # Context bypass
        pos_config_ctx = self.pos_config.with_user(self.cashier_user).with_context(
            pos_restriction_approved=True
        )
        self.assertTrue(pos_config_ctx.is_restriction_authorized('orderline_delete'))

        # Regular cashier without recent log entry
        pos_config_cashier = self.pos_config.with_user(self.cashier_user)
        self.assertFalse(pos_config_cashier.is_restriction_authorized(
            'orderline_delete', order_ref='ORDER/NO/LOG'
        ))

        # Regular cashier with recent log entry
        log = self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'orderline_delete',
            'approved_by': self.manager_user.id,
            'order_ref': 'ORDER/VALID/LOG',
            'product_id': self.product.id,
        })
        # First call authorizes and consumes approval
        self.assertTrue(pos_config_cashier.is_restriction_authorized(
            'orderline_delete', order_ref='ORDER/VALID/LOG', product_id=self.product.id
        ))
        self.assertTrue(log.is_consumed)

        # Second call is rejected because approval was consumed
        self.assertFalse(pos_config_cashier.is_restriction_authorized(
            'orderline_delete', order_ref='ORDER/VALID/LOG', product_id=self.product.id
        ))

        # Expired log entry (>10 minutes)
        expired_date = fields.Datetime.now() - timedelta(minutes=15)
        log_expired = self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'delete_order',
            'approved_by': self.manager_user.id,
            'order_ref': 'ORDER/EXPIRED',
        })
        self.env.cr.execute(
            "UPDATE pos_action_log SET create_date = %s WHERE id = %s",
            (expired_date, log_expired.id)
        )
        log_expired.invalidate_recordset(['create_date'])
        self.assertFalse(pos_config_cashier.is_restriction_authorized(
            'delete_order', order_ref='ORDER/EXPIRED'
        ))

    def test_validate_manager_pin_with_non_existent_manager_id(self):
        """Verify calling validation with a non-existent manager ID is rejected."""
        res = self.pos_config.validate_manager_pin_for_restriction(
            config_id=self.pos_config.id,
            manager_id=99999999,
            pin='7788',
            action_type='session_close',
        )
        self.assertFalse(res.get('approved'))


    def test_validate_manager_pin_cashier_fallback(self):
        """Verify cashier identity falls back to env.user when invalid or omitted."""
        res = self.pos_config.validate_manager_pin_for_restriction(
            config_id=self.pos_config.id,
            manager_id=self.manager_user.id,
            pin='7788',
            action_type='session_close',
            cashier_user_id=99999999,  # Non-existent user
        )
        self.assertTrue(res.get('approved'))
        log = self.env['pos.action.log'].search([
            ('action_type', '=', 'session_close'),
            ('approved_by', '=', self.manager_user.id),
        ], limit=1, order='create_date desc')
        self.assertEqual(log.user_id, self.env.user)

    def test_get_managers_for_approval_with_explicit_config_id(self):
        """Verify get_managers_for_approval accepts explicit config_id argument."""
        managers = self.pos_config.get_managers_for_approval(config_id=self.pos_config.id)
        self.assertIsInstance(managers, list)
        self.assertTrue(any(m['id'] == self.manager_user.id for m in managers))

    def test_is_restriction_authorized_session_close_requires_order_ref(self):
        """Verify is_restriction_authorized for session_close strictly requires order_ref."""
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'session_close',
            'approved_by': self.manager_user.id,
            'order_ref': 'POS/SESSION/001',
        })
        pos_config_cashier = self.pos_config.with_user(self.cashier_user)

        # Calling without order_ref fails
        self.assertFalse(pos_config_cashier.is_restriction_authorized('session_close', order_ref=False))

        # Calling with mismatched order_ref fails
        self.assertFalse(pos_config_cashier.is_restriction_authorized('session_close', order_ref='POS/SESSION/002'))

        # Calling with matching order_ref succeeds
        self.assertTrue(pos_config_cashier.is_restriction_authorized('session_close', order_ref='POS/SESSION/001'))

    def test_is_restriction_authorized_consume_false(self):
        """Verify is_restriction_authorized does not consume log when consume=False."""
        log = self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'orderline_quantity_update',
            'approved_by': self.manager_user.id,
            'order_ref': 'ORDER/NOCONSUME',
            'product_id': self.product.id,
        })
        pos_config_cashier = self.pos_config.with_user(self.cashier_user)
        self.assertTrue(pos_config_cashier.is_restriction_authorized(
            'orderline_quantity_update',
            order_ref='ORDER/NOCONSUME',
            product_id=self.product.id,
            consume=False
        ))
        self.assertFalse(log.is_consumed)

    def test_is_restriction_authorized_product_id_mismatch(self):
        """Verify is_restriction_authorized rejects when product_id does not match."""
        product_other = self.env['product.product'].create({
            'name': 'Other Product',
            'list_price': 10.0,
        })
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'orderline_delete',
            'approved_by': self.manager_user.id,
            'order_ref': 'ORDER/PROD/MATCH',
            'product_id': self.product.id,
        })
        pos_config_cashier = self.pos_config.with_user(self.cashier_user)
        # Calling with different product_id fails
        self.assertFalse(pos_config_cashier.is_restriction_authorized(
            'orderline_delete',
            order_ref='ORDER/PROD/MATCH',
            product_id=product_other.id
        ))

    def test_validate_manager_pin_resets_failed_attempts_on_success(self):
        """Verify successful PIN verification resets caller failed attempt counters."""
        self.cashier_user.sudo().write({'pos_pin_failed_attempts': 2})
        res = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, '7788', 'orderline_delete'
        )
        self.assertTrue(res.get('approved'))
        self.assertEqual(self.cashier_user.pos_pin_failed_attempts, 0)

    def test_validate_manager_pin_caller_lockout(self):
        """Verify caller account is locked out from requesting validation if locked."""
        lockout_time = fields.Datetime.now() + timedelta(minutes=10)
        self.cashier_user.sudo().write({'pos_pin_lockout_until': lockout_time})

        res = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, '7788', 'orderline_delete'
        )
        self.assertFalse(res.get('approved'))
        self.assertTrue(res.get('locked'))

        # Reset caller lockout
        self.cashier_user.sudo().write({'pos_pin_lockout_until': False})

    def test_get_managers_for_approval_filters_inactive_managers(self):
        """Verify get_managers_for_approval excludes inactive managers."""
        test_mgr = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Inactive Manager',
            'login': 'inactive_mgr_cfg',
            'email': 'inactive_mgr@test.com',
            'group_ids': [(6, 0, [self.pos_manager_group.id])],
            'pos_security_pin': '5566',
        })
        test_mgr.write({'active': False})
        managers = self.pos_config.with_user(self.cashier_user).get_managers_for_approval()
        manager_ids = [m['id'] for m in managers]
        self.assertNotIn(test_mgr.id, manager_ids)

    def test_handle_failed_pin_attempt_direct(self):
        """Verify _handle_failed_pin_attempt sets lockout on caller when threshold reached."""
        test_caller = self.env['res.users'].create({
            'name': 'Attempt Test Caller',
            'login': 'attempt_caller_cfg',
            'email': 'attempt_caller@test.com',
            'group_ids': [(6, 0, [self.pos_user_group.id])],
        })
        self.pos_config._handle_failed_pin_attempt(test_caller)
        self.assertEqual(test_caller.pos_pin_failed_attempts, 1)

        # Trigger lockout by reaching 5 attempts
        test_caller.sudo().write({'pos_pin_failed_attempts': 4})
        self.pos_config._handle_failed_pin_attempt(test_caller)
        self.assertTrue(test_caller.pos_pin_lockout_until)
        self.assertEqual(test_caller.pos_pin_failed_attempts, 0)

    def test_validate_manager_pin_does_not_lock_on_manager_field(self):
        """Verify manager lockout field does not block validation when caller is not locked."""
        lockout_time = fields.Datetime.now() + timedelta(minutes=10)
        self.manager_user.sudo().write({'pos_pin_lockout_until': lockout_time})
        self.cashier_user.sudo().write({'pos_pin_lockout_until': False})

        res = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, '7788', 'orderline_delete'
        )
        self.assertTrue(res.get('approved'))

        # Reset field
        self.manager_user.sudo().write({'pos_pin_lockout_until': False})

    def test_is_restriction_authorized_user_isolation(self):
        """Verify an approval created for Cashier A cannot be used by Cashier B."""
        other_cashier = self.env['res.users'].create({
            'name': 'Other Config Cashier',
            'login': 'other_cfg_cashier',
            'email': 'other_cfg@test.com',
            'group_ids': [(6, 0, [self.pos_user_group.id])],
        })
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'orderline_delete',
            'approved_by': self.manager_user.id,
            'order_ref': 'ORDER/ISOLATION/01',
            'product_id': self.product.id,
        })
        # Cashier B is not authorized
        self.assertFalse(
            self.pos_config.with_user(other_cashier).is_restriction_authorized(
                'orderline_delete',
                order_ref='ORDER/ISOLATION/01',
                product_id=self.product.id,
            )
        )
        # Cashier A is authorized
        self.assertTrue(
            self.pos_config.with_user(self.cashier_user).is_restriction_authorized(
                'orderline_delete',
                order_ref='ORDER/ISOLATION/01',
                product_id=self.product.id,
            )
        )

    def test_is_restriction_authorized_order_ref_mismatch(self):
        """Verify is_restriction_authorized returns False if order_ref does not match."""
        self.env['pos.action.log'].sudo().create({
            'user_id': self.cashier_user.id,
            'cashier_name': self.cashier_user.name,
            'action_type': 'orderline_delete',
            'approved_by': self.manager_user.id,
            'order_ref': 'ORDER/REF/EXPECTED',
            'product_id': self.product.id,
        })
        pos_config_cashier = self.pos_config.with_user(self.cashier_user)
        self.assertFalse(pos_config_cashier.is_restriction_authorized(
            'orderline_delete',
            order_ref='ORDER/REF/DIFFERENT',
            product_id=self.product.id,
        ))

    def test_validate_manager_pin_manager_without_pin(self):
        """Verify manager with no PIN configured cannot approve."""
        res = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_without_pin.id, '1234', 'orderline_delete'
        )
        self.assertFalse(res.get('approved'))

    def test_validate_manager_pin_cashier_name_fallback_to_user_name(self):
        """Verify that when manager/superuser validates with cashier_user_id and no name, user name is resolved."""
        res = self.pos_config.with_user(self.manager_user).validate_manager_pin_for_restriction(
            config_id=self.pos_config.id,
            manager_id=self.manager_user.id,
            pin='7788',
            action_type='orderline_delete',
            order_ref='ORDER/NAME/FALLBACK',
            cashier_user_id=self.cashier_user.id,
            cashier_name=False,
        )
        self.assertTrue(res.get('approved'))
        log = self.env['pos.action.log'].search([
            ('order_ref', '=', 'ORDER/NAME/FALLBACK'),
        ], limit=1)
        self.assertTrue(log)
        self.assertEqual(log.cashier_name, self.cashier_user.name)

    def test_validate_manager_pin_resets_caller_failed_attempts_on_success(self):
        """Verify caller failed attempts and lockout are cleared on successful PIN validation."""
        self.cashier_user.sudo().write({'pos_pin_failed_attempts': 3})

        res = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, '7788', 'orderline_delete'
        )
        self.assertTrue(res.get('approved'))
        self.assertEqual(self.cashier_user.pos_pin_failed_attempts, 0)

    def test_handle_failed_pin_attempt_caller_lockout(self):
        """Verify caller reaches lockout after 5 consecutive failed attempts without affecting manager."""
        caller = self.env['res.users'].create({
            'name': 'Caller Lockout Test',
            'login': 'caller_lockout_cfg',
            'email': 'caller_lockout@test.com',
            'group_ids': [(6, 0, [self.pos_user_group.id])],
        })
        self.manager_user.sudo().write({'pos_pin_failed_attempts': 0, 'pos_pin_lockout_until': False})
        caller.sudo().write({'pos_pin_failed_attempts': 4})
        self.pos_config._handle_failed_pin_attempt(caller)
        self.assertTrue(caller.pos_pin_lockout_until)
        self.assertEqual(caller.pos_pin_failed_attempts, 0)
        self.assertEqual(self.manager_user.pos_pin_failed_attempts, 0)
        self.assertFalse(self.manager_user.pos_pin_lockout_until)

    def test_handle_failed_pin_attempt_falsy_caller(self):
        """Verify _handle_failed_pin_attempt safely ignores falsy caller."""
        self.pos_config._handle_failed_pin_attempt(False)

    def test_get_managers_for_approval_group_missing(self):
        """Verify get_managers_for_approval returns empty list if group cannot be found."""
        from unittest.mock import patch
        with patch.object(type(self.env), 'ref', return_value=False):
            managers = self.pos_config.get_managers_for_approval()
            self.assertEqual(managers, [])

    def test_validate_manager_pin_rejects_stored_hash_submission(self):
        """Verify submitting the stored PBKDF2 hash itself as PIN is rejected and counted."""
        self.cashier_user.sudo().write({'pos_pin_failed_attempts': 0, 'pos_pin_lockout_until': False})
        stored_hash = self.manager_user.sudo().pos_security_pin
        res = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, stored_hash, 'orderline_delete'
        )
        self.assertFalse(res.get('approved'))
        self.assertEqual(self.cashier_user.pos_pin_failed_attempts, 1)
        self.cashier_user.sudo().write({'pos_pin_failed_attempts': 0})

    def test_validate_manager_pin_expired_lockout_allows_and_clears(self):
        """Verify expired caller lockout allows validation and clears lockout fields on success."""
        past_time = fields.Datetime.now() - timedelta(minutes=1)
        self.cashier_user.sudo().write({
            'pos_pin_failed_attempts': 0,
            'pos_pin_lockout_until': past_time,
        })
        res = self.pos_config.with_user(self.cashier_user).validate_manager_pin_for_restriction(
            self.pos_config.id, self.manager_user.id, '7788', 'orderline_delete'
        )
        self.assertTrue(res.get('approved'))
        self.assertFalse(self.cashier_user.pos_pin_lockout_until)
        self.assertEqual(self.cashier_user.pos_pin_failed_attempts, 0)




