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
import odoo.http
from unittest.mock import MagicMock
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.addons.mail_message_access import _post_init_hook


@tagged('post_install', '-at_install')
class TestMailMessageAccess(TransactionCase):
    """Test cases for Mail Message Access module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_send = cls.env.ref('mail_message_access.group_allow_send_message_btn')
        cls.group_log = cls.env.ref('mail_message_access.group_allow_log_note_btn')
        cls.group_user = cls.env.ref('base.group_user')

        # Test user with full chatter permissions
        cls.user_all = cls.env['res.users'].create({
            'name': 'Test User All',
            'login': 'test_user_all',
            'email': 'user_all@example.com',
            'group_ids': [
                Command.link(cls.group_user.id),
                Command.link(cls.group_send.id),
                Command.link(cls.group_log.id),
            ],
        })

        # Test user with Send Message only
        cls.user_send_only = cls.env['res.users'].create({
            'name': 'Test User Send Only',
            'login': 'test_user_send_only',
            'email': 'user_send_only@example.com',
            'group_ids': [
                Command.link(cls.group_user.id),
                Command.link(cls.group_send.id),
            ],
        })

        # Test user with Log Note only
        cls.user_log_only = cls.env['res.users'].create({
            'name': 'Test User Log Only',
            'login': 'test_user_log_only',
            'email': 'user_log_only@example.com',
            'group_ids': [
                Command.link(cls.group_user.id),
                Command.link(cls.group_log.id),
            ],
        })

        # Test user with neither permission
        cls.user_none = cls.env['res.users'].create({
            'name': 'Test User None',
            'login': 'test_user_none',
            'email': 'user_none@example.com',
            'group_ids': [
                Command.link(cls.group_user.id),
            ],
        })

        # Ensure group membership matches exact test fixtures
        cls.group_send.write({
            'user_ids': [
                Command.link(cls.user_all.id),
                Command.link(cls.user_send_only.id),
                Command.unlink(cls.user_log_only.id),
                Command.unlink(cls.user_none.id),
            ]
        })
        cls.group_log.write({
            'user_ids': [
                Command.link(cls.user_all.id),
                Command.link(cls.user_log_only.id),
                Command.unlink(cls.user_send_only.id),
                Command.unlink(cls.user_none.id),
            ]
        })

        # Target record inheriting mail.thread
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Chatter Partner',
            'email': 'chatter_partner@example.com',
        })

    def test_01_default_groups_have_admin_and_root(self):
        """Verify that default groups include user_admin and user_root."""
        user_admin = self.env.ref('base.user_admin')
        user_root = self.env.ref('base.user_root')

        self.assertTrue(
            user_admin.has_group('mail_message_access.group_allow_send_message_btn'),
            "Administrator should have 'Allow Send Message' permission by default."
        )
        self.assertTrue(
            user_admin.has_group('mail_message_access.group_allow_log_note_btn'),
            "Administrator should have 'Allow Log Note' permission by default."
        )
        self.assertTrue(
            user_root.has_group('mail_message_access.group_allow_send_message_btn'),
            "Root / OdooBot should have 'Allow Send Message' permission by default."
        )
        self.assertTrue(
            user_root.has_group('mail_message_access.group_allow_log_note_btn'),
            "Root / OdooBot should have 'Allow Log Note' permission by default."
        )

    def test_02_session_info_values(self):
        """Verify that session_info correctly reports access flags for each user."""
        def _get_session(user):
            mock_req = MagicMock()
            mock_req.session.uid = user.id
            mock_req.session.context = {}
            mock_req.cookies = {}
            mock_req.env = self.env(user=user)
            token = odoo.http.request_var.set(mock_req)
            try:
                return self.env['ir.http'].with_user(user).session_info()
            finally:
                odoo.http.request_var.reset(token)

        # User with both permissions
        session_all = _get_session(self.user_all)
        self.assertTrue(session_all.get('access_send_message_btn'))
        self.assertTrue(session_all.get('access_log_note_btn'))

        # User with Send Message only
        session_send = _get_session(self.user_send_only)
        self.assertTrue(session_send.get('access_send_message_btn'))
        self.assertFalse(session_send.get('access_log_note_btn'))

        # User with Log Note only
        session_log = _get_session(self.user_log_only)
        self.assertFalse(session_log.get('access_send_message_btn'))
        self.assertTrue(session_log.get('access_log_note_btn'))

        # User with neither permission
        session_none = _get_session(self.user_none)
        self.assertFalse(session_none.get('access_send_message_btn'))
        self.assertFalse(session_none.get('access_log_note_btn'))

    def test_03_send_message_permission_enforcement(self):
        """Verify backend enforcement when posting chatter messages (comments)."""
        # User with Send Message permission can post comment
        msg = self.partner.with_user(self.user_send_only).message_post(
            body='Valid message from send_only user',
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        self.assertTrue(msg, "User with Send Message permission should successfully post comment.")

        # User with full permissions can post comment
        msg2 = self.partner.with_user(self.user_all).message_post(
            body='Valid message from user_all',
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        self.assertTrue(msg2, "User with all permissions should successfully post comment.")

        # User with Log Note only cannot post comment
        with self.assertRaises(AccessError):
            self.partner.with_user(self.user_log_only).message_post(
                body='Unauthorized comment attempt',
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

        # User with no permissions cannot post comment
        with self.assertRaises(AccessError):
            self.partner.with_user(self.user_none).message_post(
                body='Unauthorized comment attempt',
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

    def test_04_log_note_permission_enforcement(self):
        """Verify backend enforcement when logging notes."""
        # User with Log Note permission can post note
        note = self.partner.with_user(self.user_log_only).message_post(
            body='Valid note from log_only user',
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )
        self.assertTrue(note, "User with Log Note permission should successfully post note.")

        # User with full permissions can post note
        note2 = self.partner.with_user(self.user_all).message_post(
            body='Valid note from user_all',
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )
        self.assertTrue(note2, "User with all permissions should successfully post note.")

        # User with Send Message only cannot post note
        with self.assertRaises(AccessError):
            self.partner.with_user(self.user_send_only).message_post(
                body='Unauthorized note attempt',
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

        # User with no permissions cannot post note
        with self.assertRaises(AccessError):
            self.partner.with_user(self.user_none).message_post(
                body='Unauthorized note attempt',
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

    def test_05_system_and_tracking_messages_allowed(self):
        """Verify automated notifications and tracking values bypass chatter restriction."""
        # User without permissions can trigger tracking/notification
        notif = self.partner.with_user(self.user_none).message_post(
            body='Automated system notification',
            message_type='notification',
        )
        self.assertTrue(notif, "System notifications must not be blocked.")

        # Tracking message must not be blocked
        tracking_msg = self.partner.with_user(self.user_none).message_post(
            body='Tracking field change',
            message_type='tracking',
        )
        self.assertTrue(tracking_msg, "Field tracking updates must not be blocked.")

    def test_06_post_init_hook_assigns_internal_users(self):
        """Verify post_init_hook assigns all internal users to the chatter groups."""
        test_new_user = self.env['res.users'].create({
            'name': 'New Internal User',
            'login': 'new_internal_user',
            'email': 'new_internal@example.com',
            'group_ids': [Command.link(self.group_user.id)],
        })

        # Remove test user from groups prior to hook execution
        self.group_send.write({'user_ids': [Command.unlink(test_new_user.id)]})
        self.group_log.write({'user_ids': [Command.unlink(test_new_user.id)]})
        self.assertFalse(test_new_user.has_group('mail_message_access.group_allow_send_message_btn'))
        self.assertFalse(test_new_user.has_group('mail_message_access.group_allow_log_note_btn'))

        # Run post_init_hook
        _post_init_hook(self.env)

        self.assertTrue(
            test_new_user.has_group('mail_message_access.group_allow_send_message_btn'),
            "Post init hook should assign internal user to Allow Send Message."
        )
        self.assertTrue(
            test_new_user.has_group('mail_message_access.group_allow_log_note_btn'),
            "Post init hook should assign internal user to Allow Log Note."
        )
