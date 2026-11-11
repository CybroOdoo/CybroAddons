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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):
    """Unit tests for res.users model additions."""

    @classmethod
    def setUpClass(cls):
        """Set up test users and permission groups."""
        super().setUpClass()
        cls.pos_manager_group = cls.env.ref('point_of_sale.group_pos_manager')
        cls.pos_user_group = cls.env.ref('point_of_sale.group_pos_user')

        cls.manager_user = cls.env['res.users'].create({
            'name': 'Test Manager User',
            'login': 'test_manager_user_pin',
            'email': 'test_manager_pin@example.com',
            'group_ids': [(6, 0, [cls.pos_manager_group.id, cls.pos_user_group.id])],
            'pos_security_pin': '4321',
        })

    def test_pos_security_pin_assignment(self):
        """Verify that pos_security_pin is stored as a salted PBKDF2-SHA512 hash."""
        self.assertNotEqual(self.manager_user.pos_security_pin, '4321')
        self.assertTrue(self.manager_user.pos_security_pin.startswith('$pbkdf2-sha512$'))
        self.assertTrue(self.manager_user.check_pos_security_pin('4321'))
        self.assertFalse(self.manager_user.check_pos_security_pin('wrong_pin'))
        # Submitting the stored hash itself must never validate
        self.assertFalse(self.manager_user.check_pos_security_pin(self.manager_user.pos_security_pin))

        # Verify distinct salts produce distinct hashes for the same PIN
        other_user = self.env['res.users'].create({
            'name': 'Second Manager User',
            'login': 'test_manager_user_pin_2',
            'email': 'test_manager_pin_2@example.com',
            'group_ids': [(6, 0, [self.pos_manager_group.id, self.pos_user_group.id])],
            'pos_security_pin': '4321',
        })
        self.assertNotEqual(other_user.pos_security_pin, self.manager_user.pos_security_pin)

    def test_pos_security_pin_not_copied(self):
        """Verify that pos_security_pin is not copied when user record is duplicated."""
        cloned_user = self.manager_user.copy({'login': 'cloned_manager_login'})
        self.assertFalse(cloned_user.pos_security_pin)

    def test_pos_security_pin_update(self):
        """Verify that pos_security_pin can be updated and cleared."""
        self.manager_user.write({'pos_security_pin': '9876'})
        self.assertNotEqual(self.manager_user.pos_security_pin, '9876')
        self.assertTrue(self.manager_user.check_pos_security_pin('9876'))
        self.assertFalse(self.manager_user.check_pos_security_pin('4321'))
        self.manager_user.write({'pos_security_pin': False})
        self.assertFalse(self.manager_user.pos_security_pin)

    def test_pos_security_pin_field_definition(self):
        """Verify field definition has appropriate group and copy protection."""
        field = self.env['res.users']._fields['pos_security_pin']
        self.assertEqual(field.groups, 'point_of_sale.group_pos_manager')
        self.assertFalse(field.copy)

    def test_rate_limiting_fields_definition(self):
        """Verify rate-limiting and lockout fields on res.users."""
        attempts_field = self.env['res.users']._fields['pos_pin_failed_attempts']
        lockout_field = self.env['res.users']._fields['pos_pin_lockout_until']
        self.assertEqual(attempts_field.groups, 'point_of_sale.group_pos_manager')
        self.assertFalse(attempts_field.copy)
        self.assertEqual(self.manager_user.pos_pin_failed_attempts, 0)
        self.assertEqual(lockout_field.groups, 'point_of_sale.group_pos_manager')
        self.assertFalse(lockout_field.copy)

    def test_pin_crypt_context(self):
        """Verify _pin_crypt_context enforces pbkdf2_sha512 only without plaintext."""
        ctx = self.env['res.users']._pin_crypt_context()
        self.assertEqual(tuple(ctx.schemes()), ('pbkdf2_sha512',))
        self.assertNotIn('plaintext', ctx.schemes())
        self.assertIsNone(ctx.identify('plaintext_pin'))

    def test_hash_pin_helper_edge_cases(self):
        """Verify _hash_pin handles empty, whitespace, padded, integer, and hash inputs."""
        self.assertFalse(self.env['res.users']._hash_pin(False))
        self.assertFalse(self.env['res.users']._hash_pin(None))
        self.assertFalse(self.env['res.users']._hash_pin(""))
        self.assertFalse(self.env['res.users']._hash_pin("    "))

        # Integer and whitespace-padded PINs are normalized and hashed
        int_hash = self.env['res.users']._hash_pin(1234)
        self.assertTrue(int_hash.startswith('$pbkdf2-sha512$'))
        self.assertTrue(self.env['res.users']._pin_crypt_context().verify('1234', int_hash))

        # Must never pass through 64-hex strings or existing hashes unchanged
        hex_64 = "0" * 64
        self.assertNotEqual(self.env['res.users']._hash_pin(hex_64), hex_64)
        hashed = self.env['res.users']._hash_pin("1234")
        self.assertTrue(hashed.startswith('$pbkdf2-sha512$'))
        self.assertNotEqual(self.env['res.users']._hash_pin(hashed), hashed)

    def test_check_pos_security_pin_edge_cases(self):
        """Verify check_pos_security_pin rejects empty, plaintext, and unsalted hashes."""
        # Falsy candidate PIN returns False
        self.assertFalse(self.manager_user.check_pos_security_pin(False))
        self.assertFalse(self.manager_user.check_pos_security_pin(None))
        self.assertFalse(self.manager_user.check_pos_security_pin(""))
        self.assertFalse(self.manager_user.check_pos_security_pin("   "))

        # User with no PIN configured returns False
        user_no_pin = self.env['res.users'].create({
            'name': 'User With No Pin',
            'login': 'user_no_pin_test',
            'email': 'nopin@test.com',
            'pos_security_pin': False,
        })
        self.assertFalse(user_no_pin.check_pos_security_pin("1234"))

        # Plain-text PIN stored directly in DB must be rejected (no plaintext fallback)
        self.env.cr.execute(
            "UPDATE res_users SET pos_security_pin = 'plain999' WHERE id = %s",
            (user_no_pin.id,)
        )
        user_no_pin.invalidate_recordset(['pos_security_pin'])
        self.assertFalse(user_no_pin.check_pos_security_pin("plain999"))

        # Unsalted SHA-256 hex stored directly in DB must also be rejected
        self.env.cr.execute(
            "UPDATE res_users SET pos_security_pin = %s WHERE id = %s",
            ("a" * 64, user_no_pin.id)
        )
        user_no_pin.invalidate_recordset(['pos_security_pin'])
        self.assertFalse(user_no_pin.check_pos_security_pin("a" * 64))

    def test_user_create_multi_batch(self):
        """Verify model_create_multi handles batch creations with and without PIN."""
        users = self.env['res.users'].create([
            {
                'name': 'Batch User 1',
                'login': 'batch_user_1_test',
                'email': 'batch1@test.com',
                'pos_security_pin': '1111',
            },
            {
                'name': 'Batch User 2',
                'login': 'batch_user_2_test',
                'email': 'batch2@test.com',
                'pos_security_pin': False,
            },
        ])
        self.assertTrue(users[0].check_pos_security_pin('1111'))
        self.assertFalse(users[1].pos_security_pin)

    def test_user_write_preserves_pin_when_not_in_vals(self):
        """Verify writing other fields does not alter existing hashed PIN."""
        orig_pin_hash = self.manager_user.pos_security_pin
        self.manager_user.write({'name': 'Updated Manager Name'})
        self.assertEqual(self.manager_user.pos_security_pin, orig_pin_hash)
        self.assertTrue(self.manager_user.check_pos_security_pin('4321'))
        self.assertTrue(self.manager_user.check_pos_security_pin(' 4321 '))

    def test_whitespace_pin_in_create_and_write_clears_pin(self):
        """Verify whitespace-only PIN values in create/write resolve to False."""
        ws_user = self.env['res.users'].create({
            'name': 'Whitespace Pin User',
            'login': 'ws_pin_user_test',
            'email': 'ws_pin@test.com',
            'pos_security_pin': '   ',
        })
        self.assertFalse(ws_user.pos_security_pin)

        ws_user.write({'pos_security_pin': '5678'})
        self.assertTrue(ws_user.check_pos_security_pin('5678'))
        ws_user.write({'pos_security_pin': '   '})
        self.assertFalse(ws_user.pos_security_pin)



