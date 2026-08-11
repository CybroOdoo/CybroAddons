"""Tests for AI Chat Session model."""
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


class TestAIChatSession(AIConnectorAgentTestCase):
    """Tests for ai.chat.session model."""

    def test_get_or_create_session_reuses_active_session(self):
        """Test that get_or_create_session reuses an existing active session."""
        session_model = self.env["ai.chat.session"]
        first_session = session_model.get_or_create_session(self.provider.id, self.model.id, self.env.user.id)
        second_session = session_model.get_or_create_session(self.provider.id, self.model.id, self.env.user.id)

        self.assertEqual(first_session, second_session)
        self.assertEqual(first_session.ai_agent_id, self.provider)
        self.assertEqual(first_session.ai_model_id, self.model)
        self.assertIn(self.provider.name, first_session.name)
        self.assertIn(self.model.modelId, first_session.name)
