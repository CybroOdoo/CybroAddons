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

import json
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.vibe_coding_assistant.services.provider_base import AIProviderError

from .common import BUILD_PROMPT, VibeCommon, fake_provider

GET_PROVIDER = (
    "odoo.addons.vibe_coding_assistant.models.vibe_conversation.get_provider"
)

@tagged("post_install", "-at_install")
class TestConversation(VibeCommon):

    def setUp(self):
        super().setUp()
        self.conv = self._make_conversation(name="New Chat")
        self.conv_a = self.conv.with_user(self.user_a)

    # ── action_send_message ───────────────────────────────────────────────

    def test_empty_message(self):
        with self.assertRaises(UserError):
            self.conv_a.action_send_message("   ")

    def test_no_active_config(self):
        conv = self._make_conversation(user=self.user_b).with_user(self.user_b)
        with self.assertRaises(UserError):
            conv.action_send_message(BUILD_PROMPT)

    def test_offtopic_message_skips_provider(self):
        with patch(GET_PROVIDER) as mock:
            payload = self.conv_a.action_send_message("hello")
        mock.assert_not_called()
        roles = [m["role"] for m in payload["messages"]]
        self.assertEqual(roles, ["user", "assistant"])
        self.assertEqual(self.conv.state, "active")

    def test_successful_generation(self):
        with patch(GET_PROVIDER, return_value=fake_provider()):
            payload = self.conv_a.action_send_message(BUILD_PROMPT)
        module = self.conv.generated_module_ids
        self.assertEqual(len(module), 1)
        self.assertEqual(module.technical_name, "library_book")
        self.assertIn(module.validation_state, ("valid", "invalid"))
        self.assertTrue(module.file_ids)
        self.assertEqual(self.conv.state, "active")
        self.assertEqual(self.conv.provider_config_id, self.config_a)
        self.assertEqual(self.conv.tokens_total, 30)
        self.assertEqual(self.conv.tokens_input_total, 10)
        self.assertEqual(self.conv.tokens_output_total, 20)
        self.assertTrue(payload["conversation"]["can_refine"])
        self.assertEqual(self.conv.name, BUILD_PROMPT)

    def test_provider_error_is_reported(self):
        provider = fake_provider(error=AIProviderError("boom"))
        with patch(GET_PROVIDER, return_value=provider):
            payload = self.conv_a.action_send_message(BUILD_PROMPT)
        self.assertFalse(self.conv.generated_module_ids)
        self.assertIn("Provider error", payload["messages"][-1]["content"])

    def test_unparsable_reply_still_records_tokens(self):
        provider = fake_provider(reply=("not json at all", {
            "input": 3, "output": 4, "total": 7}))
        with patch(GET_PROVIDER, return_value=provider):
            self.conv_a.action_send_message(BUILD_PROMPT)
        self.assertFalse(self.conv.generated_module_ids)
        self.assertEqual(self.conv.tokens_total, 7)
        self.assertEqual(self.conv.provider_config_id, self.config_a)

    # ── action_refine_module ──────────────────────────────────────────────

    def test_refine_validations(self):
        with self.assertRaises(UserError):
            self.conv_a.action_refine_module("  ")
        with self.assertRaises(UserError):
            self.conv_a.action_refine_module("add a field")  # nothing yet
        self._make_module(self.conv)
        conv_b = self._make_conversation(user=self.user_b)
        self._make_module(conv_b)
        with self.assertRaises(UserError):
            conv_b.with_user(self.user_b).action_refine_module("add a field")

    def test_refine_success(self):
        previous = self._make_module(self.conv)
        with patch(GET_PROVIDER, return_value=fake_provider()):
            payload = self.conv_a.action_refine_module("add an ISBN field")
        refined = self.conv.generated_module_ids - previous
        self.assertEqual(len(refined), 1)
        self.assertEqual(refined.revision_number, 2)
        self.assertEqual(refined.parent_module_id, previous)
        self.assertTrue(refined.is_refinement)
        self.assertEqual(payload["conversation"]["latest_module_revision"], 2)

    def test_refine_with_broken_manifest_data(self):
        self._make_module(self.conv, manifest_data="{broken")
        with patch(GET_PROVIDER, return_value=fake_provider()):
            self.conv_a.action_refine_module("tweak")
        self.assertEqual(len(self.conv.generated_module_ids), 2)

    def test_refine_provider_error(self):
        self._make_module(self.conv)
        provider = fake_provider(error=AIProviderError("down"))
        with patch(GET_PROVIDER, return_value=provider):
            payload = self.conv_a.action_refine_module("tweak")
        self.assertEqual(len(self.conv.generated_module_ids), 1)
        self.assertIn("Provider error", payload["messages"][-1]["content"])

    def test_refine_unparsable_reply(self):
        self._make_module(self.conv)
        provider = fake_provider(reply=("garbage", {
            "input": 1, "output": 2, "total": 3}))
        with patch(GET_PROVIDER, return_value=provider):
            self.conv_a.action_refine_module("tweak")
        self.assertEqual(len(self.conv.generated_module_ids), 1)
        self.assertEqual(self.conv.tokens_total, 3)

    # ── misc public API ───────────────────────────────────────────────────

    def test_load_messages_payload(self):
        module = self._make_module(self.conv, validation_errors=json.dumps(
            [{"file": "x", "line": 1, "message": "bad"}]))
        self.env["vibe.message"].create({
            "conversation_id": self.conv.id, "role": "assistant",
            "content": "Generated", "generated_module_id": module.id,
        })
        payload = self.conv.load_messages()
        msg = payload["messages"][0]
        self.assertEqual(msg["generated_module_technical_name"], "library_book")
        self.assertEqual(msg["generated_module_version"], "20.0.1.0.0")
        self.assertEqual(msg["validation_error_count"], 1)
        self.assertEqual(msg["generated_module_file_count"], 3)

    def test_archive_and_export_action(self):
        self.assertTrue(self.conv.action_archive())
        self.assertEqual(self.conv.state, "archived")
        action = self.conv.action_export_json()
        self.assertEqual(action["url"], "/vibe/conversation/%d/export" % self.conv.id)
