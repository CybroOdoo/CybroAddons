"""Tests for AI Connector Controller."""
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class AIConnectorAgentTestCase(TransactionCase):
    """Base test case for AI Connector Agent."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for AI Connector Agent tests."""
        super().setUpClass()
        cls.provider = cls.env["ai.providers"].create({
            "name": "OpenAI",
            "api_key": "test-key",
            "api_base_url": "https://api.openai.com",
        })
        cls.model = cls.env["ai.model"].create({
            "modelId": "gpt-4o-mini",
            "object": "model",
        })
        cls.provider.ai_model_ids = [cls.model.id]
        cls.controller_patch_path = "odoo.addons.ai_connector_agent.controller.ai_connector_agent"

    def _controller(self):
        """Get an instance of AI Chat Controller."""
        from odoo.addons.ai_connector_agent.controller.ai_connector_agent import AiChatController

        return AiChatController()

    def _request_stub(self):
        """Get a stub for the request object."""
        from types import SimpleNamespace

        return SimpleNamespace(env=self.env)


class TestAIConnectorController(AIConnectorAgentTestCase):
    """Tests for AI Connector Controller."""

    def test_send_message_creates_messages_and_attachments(self):
        """Test that send_message creates messages and handles attachments correctly."""
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
        """Test that get_messages returns the correct message history for a session."""
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
        """Test that get_active_provider falls back to the first available provider and model if none are set for the user."""
        self.env.user.write({
            "active_ai_agent_id": False,
            "active_ai_model_id": False,
        })
        controller = self._controller()

        with patch(f"{self.controller_patch_path}.request", self._request_stub()):
            result = controller.get_active_provider()

        self.assertTrue(result["success"])
        provider = self.env["ai.providers"].browse(result["agent_id"])
        model = self.env["ai.model"].browse(result["model_id"])
        self.assertTrue(provider.exists())
        self.assertTrue(model.exists())
        self.assertIn(model, provider.ai_model_ids)

    def test_save_active_config_updates_user_preferences(self):
        """Test that save_active_config updates the user's active AI agent and model preferences."""
        other_model = self.env["ai.model"].create({"modelId": "gpt-4.1-mini"})
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
