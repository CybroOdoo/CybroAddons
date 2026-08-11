"""Tests for AI Providers model."""
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class MockResponse:
    """Mock response object for requests."""

    def __init__(self, status_code=200, payload=None, text=""):
        """Initialize mock response."""
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        """Mock json method."""
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


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


class TestAIProviders(AIConnectorAgentTestCase):
    """Tests for ai.providers model."""

    def test_action_fetch_models_creates_and_links_records(self):
        """Test that fetching models creates new model records and links them to the provider."""
        payload = {
            "data": [
                {"id": "gpt-4.1", "object": "model", "version": "2026-01"},
                {"id": self.model.modelId, "object": "model"},
            ]
        }

        with patch("odoo.addons.ai_connector_agent.models.ai_providers.requests.get", return_value=MockResponse(payload=payload)) as mock_get:
            self.provider.action_fetch_models()

        self.assertEqual(mock_get.call_args.args[0], "https://api.openai.com/v1/models")
        self.assertEqual(mock_get.call_args.kwargs["headers"]["Authorization"], "Bearer test-key")
        model_ids = self.provider.ai_model_ids.mapped("modelId")
        self.assertIn("gpt-4.1", model_ids)
        self.assertIn("gpt-4o-mini", model_ids)
        linked_model = self.provider.ai_model_ids.filtered(lambda m: m.modelId == self.model.modelId)
        self.assertTrue(linked_model)

    def test_action_fetch_models_rejects_invalid_json_structure(self):
        """Test that fetching models raises an error if the response JSON structure is invalid."""
        with patch("odoo.addons.ai_connector_agent.models.ai_providers.requests.get", return_value=MockResponse(payload=["bad-data"])):
            with self.assertRaises(UserError):
                self.provider.action_fetch_models()
