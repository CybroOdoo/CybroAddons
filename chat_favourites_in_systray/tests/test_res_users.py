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
"""Test suite for ResUsers model extensions in Chat Favourites In Systray."""
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user
from odoo.addons.mail.tools.discuss import Store


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):
    """Test suite covering ResUsers model modifications and _store_init_fields."""

    @classmethod
    def setUpClass(cls):
        """Set up test users and channels for model tests."""
        super().setUpClass()
        cls.test_user = new_test_user(
            cls.env,
            login='res_users_test_user',
            name='Res Users Test User',
            groups='base.group_user',
        )
        cls.channel_a = cls.env['discuss.channel'].create({
            'name': 'Channel Alpha',
            'channel_type': 'channel',
        })
        cls.channel_b = cls.env['discuss.channel'].create({
            'name': 'Channel Beta',
            'channel_type': 'channel',
        })

    def test_mail_channel_ids_field(self):
        """Test mail_channel_ids field link, unlink and clear operations."""
        self.assertFalse(self.test_user.mail_channel_ids)

        # Link channels
        self.test_user.write({
            'mail_channel_ids': [
                fields.Command.link(self.channel_a.id),
                fields.Command.link(self.channel_b.id),
            ],
        })
        self.assertEqual(len(self.test_user.mail_channel_ids), 2)
        self.assertIn(self.channel_a, self.test_user.mail_channel_ids)
        self.assertIn(self.channel_b, self.test_user.mail_channel_ids)

        # Unlink one channel
        self.test_user.write({
            'mail_channel_ids': [fields.Command.unlink(self.channel_a.id)],
        })
        self.assertEqual(self.test_user.mail_channel_ids, self.channel_b)

        # Clear remaining
        self.test_user.write({
            'mail_channel_ids': [fields.Command.clear()],
        })
        self.assertFalse(self.test_user.mail_channel_ids)

    def test_store_init_fields(self):
        """Test _store_init_fields appends mail_channel_ids as Store.Many relation."""
        store = Store(self.test_user)
        field_list = Store.FieldList(store, self.test_user)

        result = self.test_user._store_init_fields(field_list)
        self.assertIsNone(result)

        # Verify that mail_channel_ids is registered as a Store.Many relation
        many_relations = [
            item for item in field_list
            if isinstance(item, Store.Many) and item.field_name == 'mail_channel_ids'
        ]
        self.assertTrue(
            many_relations,
            "Store.FieldList should include a Store.Many relation for 'mail_channel_ids'.",
        )

        # Verify super()._store_init_fields was also called
        has_notification_type = any(
            item == 'notification_type' for item in field_list
        )
        self.assertTrue(
            has_notification_type,
            "Super fields such as 'notification_type' should still be present in field_list.",
        )
