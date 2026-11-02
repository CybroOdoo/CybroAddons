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
import base64
from unittest.mock import MagicMock

from odoo.tests.common import TransactionCase

CONTROLLER_PATH = 'odoo.addons.ai_connector_agent.controllers.ai_connector_agent'
PROVIDERS_PATH = 'odoo.addons.ai_connector_agent.models.ai_providers'

# 1x1 transparent PNG
PNG_B64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA'
    '60e6kgAAAABJRU5ErkJggg=='
)


def make_response(status=200, json_data=None, text='', json_raises=False):
    """Build a fake ``requests`` response."""
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    if json_raises:
        resp.json.side_effect = ValueError('no json')
    else:
        resp.json.return_value = json_data if json_data is not None else {}
    return resp


class AiConnectorCommon(TransactionCase):
    """Base class creating a provider, a model, a session and a second user."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Provider = cls.env['ai.provider']
        cls.Model = cls.env['ai.model']
        cls.Session = cls.env['ai.chat.session']
        cls.Message = cls.env['ai.chat.message']

        cls.model_a = cls.Model.create({'model_ref_id': 'test-model-a'})
        cls.model_b = cls.Model.create({'model_ref_id': 'test-model-b'})
        cls.provider = cls.Provider.create({
            'name': 'OpenAI Test',
            'api_key': 'sk-test',
            'api_base_url': 'https://api.openai.com',
            'ai_model_ids': [(6, 0, [cls.model_a.id, cls.model_b.id])],
        })
        cls.other_user = cls.env['res.users'].create({
            'name': 'Other Chat User',
            'login': 'other_chat_user',
            'email': 'other_chat_user@example.com',
        })

    def _make_provider(self, name, base_url, models=None):
        vals = {'name': name, 'api_key': 'key', 'api_base_url': base_url}
        if models:
            vals['ai_model_ids'] = [(6, 0, models.ids)]
        return self.Provider.create(vals)

    def _make_session(self, provider=None, model=None, user=None):
        return self.Session.create({
            'name': 'Test Session',
            'ai_agent_id': (provider or self.provider).id,
            'ai_model_id': (model or self.model_a).id,
            'user_id': (user or self.env.user).id,
        })

    def _add_message(self, session, mtype='user', content='hello'):
        return self.Message.create({
            'session_id': session.id,
            'message_type': mtype,
            'content': content,
        })

    def _make_attachment(self, name='pic.png', data=PNG_B64):
        return self.env['ir.attachment'].create({
            'name': name,
            'raw': base64.b64decode(data),
            'res_model': 'ai.chat.message',
        })

    @staticmethod
    def _b64(text):
        return base64.b64encode(text.encode()).decode()
