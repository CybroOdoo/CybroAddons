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
class TestResUsers(TransactionCase):
    """Test cases for res.users model extension in mail_push_notification."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref('base.group_user')
        cls.group_portal = cls.env.ref('base.group_portal', raise_if_not_found=False)
        cls.groups_field = 'group_ids' if 'group_ids' in cls.env['res.users']._fields else 'groups_id'

        cls.internal_user = cls.env['res.users'].create({
            'name': 'Test Internal User',
            'login': 'test_internal_user',
            'email': 'internal_user@example.com',
            cls.groups_field: [(6, 0, [cls.group_user.id])],
        })

        portal_vals = {
            'name': 'Test Portal User',
            'login': 'test_portal_user',
            'email': 'portal_user@example.com',
        }
        if cls.group_portal:
            portal_vals[cls.groups_field] = [(6, 0, [cls.group_portal.id])]
        cls.portal_user = cls.env['res.users'].create(portal_vals)

    def test_has_push_notification_permission(self):
        """Test has_push_notification_permission returns True for internal users
        and False for external/portal/public users."""
        # 1. Internal user should have push notification permission
        self.assertTrue(
            self.internal_user.has_push_notification_permission(),
            "Internal user (member of base.group_user) must have push notification permission."
        )

        # 2. Portal user should NOT have push notification permission
        self.assertFalse(
            self.portal_user.has_push_notification_permission(),
            "Portal user must not have push notification permission."
        )

        # 3. Superuser/Admin user should have push notification permission
        admin_user = self.env.ref('base.user_admin')
        self.assertTrue(
            admin_user.has_push_notification_permission(),
            "Admin user must have push notification permission."
        )

        # 4. Public user should NOT have push notification permission
        public_user = self.env.ref('base.public_user', raise_if_not_found=False)
        if public_user:
            self.assertFalse(
                public_user.has_push_notification_permission(),
                "Public user must not have push notification permission."
            )

        # 5. Revoking group_user removes permission
        groups_field = self.groups_field
        test_toggle_user = self.env['res.users'].create({
            'name': 'Toggle User',
            'login': 'test_toggle_user',
            'email': 'toggle_user@example.com',
            groups_field: [(6, 0, [self.group_user.id])],
        })
        self.assertTrue(test_toggle_user.has_push_notification_permission())
        test_toggle_user.write({groups_field: [(3, self.group_user.id)]})
        self.assertFalse(test_toggle_user.has_push_notification_permission())
