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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPushNotification(TransactionCase):
    """Test suite for push.notification model in mail_push_notification."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = cls.env['res.users'].create({
            'name': 'Push Device User',
            'login': 'push_device_user',
            'email': 'push_device@example.com',
        })

    def test_push_notification(self):
        """Test push.notification record creation, search, update and unlink."""
        # 1. Create a push notification record
        record = self.env['push.notification'].create({
            'user_id': self.test_user.id,
            'register_id': 'token_xyz_12345',
        })
        self.assertTrue(record.id)
        self.assertEqual(record.user_id, self.test_user)
        self.assertEqual(record.register_id, 'token_xyz_12345')

        # 2. Search by domain (matching how mail.thread searches)
        found = self.env['push.notification'].search([('user_id', 'in', [self.test_user.id])])
        self.assertIn(record, found)

        # 3. Multiple tokens for the same user (e.g. mobile and desktop devices)
        record2 = self.env['push.notification'].create({
            'user_id': self.test_user.id,
            'register_id': 'token_mobile_67890',
        })
        user_tokens = self.env['push.notification'].search([('user_id', '=', self.test_user.id)])
        token_strings = [r.register_id for r in user_tokens]
        self.assertIn('token_xyz_12345', token_strings)
        self.assertIn('token_mobile_67890', token_strings)

        # 4. Update token
        record.write({'register_id': 'token_updated_99999'})
        self.assertEqual(record.register_id, 'token_updated_99999')

        # 5. Delete token
        record.unlink()
        remaining = self.env['push.notification'].search([('register_id', '=', 'token_updated_99999')])
        self.assertFalse(remaining)

