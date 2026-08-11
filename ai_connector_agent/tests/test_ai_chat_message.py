"""Tests for AI Chat Message model."""
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


class TestAIChatMessage(AIConnectorAgentTestCase):
    """Tests for ai.chat.message model."""

    def test_create_updates_session_last_message_date(self):
        """Test that creating a message updates the session's last message date."""
        session = self.env["ai.chat.session"].create({
            "name": "Session",
            "ai_agent_id": self.provider.id,
            "ai_model_id": self.model.id,
            "user_id": self.env.user.id,
        })

        message = self.env["ai.chat.message"].create({
            "session_id": session.id,
            "message_type": "user",
            "content": "Hello",
        })

        self.assertEqual(session.last_message_date, message.timestamp)
