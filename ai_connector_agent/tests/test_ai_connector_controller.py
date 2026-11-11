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

from types import SimpleNamespace
from unittest.mock import patch

from .common import AIConnectorAgentTestCase


class TestAIConnectorController(AIConnectorAgentTestCase):
    def test_send_message_creates_messages_and_attachments(self):
        controller = self._controller()
        image_data = "data:image/png;base64,aGVsbG8="

        with patch(f"{self.controller_patch_path}.request", self._request_stub()), \
             patch.object(type(controller), "_get_ai_response", return_value="Assistant reply"):
            result = controller.send_message(
                message="Hello AI",
                ai_agent_id=str(self.provider.id),
                ai_model_id=str(self.model.id),
                attachments=[{"name": "image.png", "data": image_data}],
            )

        self.assertTrue(result["success"])
        session = self.env["ai.chat.session"].browse(result["session_id"])
        self.assertEqual(len(session.message_ids), 2)
        user_message = session.message_ids.filtered(lambda m: m.message_type == "user")
        ai_message = session.message_ids.filtered(lambda m: m.message_type == "ai")
        self.assertEqual(user_message.content, "Hello AI")
        self.assertEqual(ai_message.content, "Assistant reply")
        self.assertEqual(len(user_message.attachment_ids), 1)
        self.assertEqual(user_message.attachment_ids.res_id, user_message.id)
        self.assertEqual(user_message.attachment_ids.datas, b"aGVsbG8=")

    def test_get_messages_returns_existing_session_history(self):
        session = self.env["ai.chat.session"].create({
            "name": "Session",
            "ai_agent_id": self.provider.id,
            "ai_model_id": self.model.id,
            "user_id": self.env.user.id,
        })
        self.env["ai.chat.message"].create({
            "session_id": session.id,
            "message_type": "user",
            "content": "First",
        })
        self.env["ai.chat.message"].create({
            "session_id": session.id,
            "message_type": "ai",
            "content": "Second",
        })
        controller = self._controller()

        with patch(f"{self.controller_patch_path}.request", self._request_stub()):
            result = controller.get_messages(
                ai_agent_id=str(self.provider.id),
                ai_model_id=str(self.model.id),
                session_id=str(session.id),
            )

        self.assertTrue(result["success"])
        self.assertEqual(result["session_id"], session.id)
        self.assertEqual([message["content"] for message in result["messages"]], ["First", "Second"])

    def test_get_active_provider_falls_back_to_first_provider_model(self):
        self.env.user.write({
            "active_ai_agent_id": False,
            "active_ai_model_id": False,
        })
        controller = self._controller()

        with patch(f"{self.controller_patch_path}.request", self._request_stub()):
            result = controller.get_active_provider()

        self.assertTrue(result["success"])
        self.assertEqual(result["agent_id"], self.provider.id)
        self.assertEqual(result["model_id"], self.model.id)

    def test_save_active_config_updates_user_preferences(self):
        other_model = self.env["ai.model"].create({"model_id": "gpt-4.1-mini"})
        self.provider.ai_model_ids = [(4, other_model.id)]
        controller = self._controller()

        with patch(f"{self.controller_patch_path}.request", self._request_stub()):
            result = controller.save_active_config(
                ai_agent_id=str(self.provider.id),
                ai_model_id=str(other_model.id),
            )

        self.assertTrue(result["success"])
        self.assertEqual(self.env.user.active_ai_agent_id, self.provider)
        self.assertEqual(self.env.user.active_ai_model_id, other_model)

    def test_save_active_config_regular_user(self):
        regular_user = self.env["res.users"].create({
            "name": "Standard User",
            "login": "standard_user_pref",
            "email": "standard@example.com",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        other_model = self.env["ai.model"].create({"model_id": "gpt-4.1-nano"})
        self.provider.ai_model_ids = [(4, other_model.id)]
        controller = self._controller()

        reg_request = SimpleNamespace(env=self.env(user=regular_user))
        with patch(f"{self.controller_patch_path}.request", reg_request):
            result = controller.save_active_config(
                ai_agent_id=str(self.provider.id),
                ai_model_id=str(other_model.id),
            )

        self.assertTrue(result["success"])
        self.assertEqual(regular_user.active_ai_agent_id, self.provider)
        self.assertEqual(regular_user.active_ai_model_id, other_model)

    def test_delete_session_checks_ownership(self):
        other_user = self.env["res.users"].create({
            "name": "Other User",
            "login": "other_user_test",
            "email": "other@example.com",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        session = self.env["ai.chat.session"].create({
            "name": "Other User Session",
            "ai_agent_id": self.provider.id,
            "ai_model_id": self.model.id,
            "user_id": other_user.id,
        })
        controller = self._controller()

        # Normal user cannot delete someone else's session
        other_request = SimpleNamespace(env=self.env(user=other_user))
        user_request = SimpleNamespace(env=self.env)
        # Assuming self.env.user is admin, let's create a regular user for current user
        reg_user = self.env["res.users"].create({
            "name": "Regular User",
            "login": "reg_user_test",
            "email": "reg@example.com",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        reg_request = SimpleNamespace(env=self.env(user=reg_user))

        with patch(f"{self.controller_patch_path}.request", reg_request):
            res = controller.delete_session(session_id=session.id)
            self.assertEqual(res.get("error"), "Access denied")
            self.assertTrue(session.exists())

            # Also cannot get messages of other user's session
            res_msg = controller.get_messages(
                ai_agent_id=str(self.provider.id),
                ai_model_id=str(self.model.id),
                session_id=str(session.id),
            )
            self.assertIn("error", res_msg)

        # Owner can delete
        with patch(f"{self.controller_patch_path}.request", other_request):
            res = controller.delete_session(session_id=session.id)
            self.assertTrue(res.get("success"))
            self.assertFalse(session.exists())
