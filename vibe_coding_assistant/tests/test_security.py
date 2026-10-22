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

from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import VibeCommon

@tagged("post_install", "-at_install")
class TestSecurity(VibeCommon):

    def setUp(self):
        super().setUp()
        self.conv_a = self._make_conversation(user=self.user_a)
        self.conv_b = self._make_conversation(user=self.user_b)
        self.module_a = self._make_module(self.conv_a)
        self.module_b = self._make_module(self.conv_b)
        self.msg_b = self.env["vibe.message"].create({
            "conversation_id": self.conv_b.id, "role": "user", "content": "b"})

    def test_conversations_are_private(self):
        found = self.env["vibe.conversation"].with_user(self.user_a).search([])
        self.assertIn(self.conv_a, found)
        self.assertNotIn(self.conv_b, found)
        with self.assertRaises(AccessError):
            self.conv_b.with_user(self.user_a).read(["name"])

    def test_modules_files_messages_are_private(self):
        as_a = self.user_a
        modules = self.env["vibe.generated.module"].with_user(as_a).search([])
        self.assertEqual(modules, self.module_a)
        files = self.env["vibe.generated.file"].with_user(as_a).search([])
        self.assertEqual(files.mapped("module_id"), self.module_a)
        messages = self.env["vibe.message"].with_user(as_a).search([])
        self.assertNotIn(self.msg_b, messages)

    def test_regular_users_cannot_edit_providers(self):
        providers = self.env["ai.provider"].with_user(self.user_a)
        self.assertTrue(providers.search([]))  # read allowed
        with self.assertRaises(AccessError):
            providers.browse(self.provider.id).write({"name": "Hacked"})

    def test_dashboard_is_admin_only(self):
        with self.assertRaises(AccessError):
            self.env["vibe.dashboard"].with_user(self.user_a).create({})
