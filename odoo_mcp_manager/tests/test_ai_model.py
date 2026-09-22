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

from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestAiModel(TransactionCase):

    def setUp(self):
        super(TestAiModel, self).setUp()
        self.provider = self.env['ai.provider'].create({
            'name': 'Model Provider',
            'service': 'openai',
            'api_key': 'fake',
        })
        self.model = self.env['ai.model'].create({
            'name': 'test-model',
            'provider_id': self.provider.id,
            'model_use': 'chat',
        })

    def test_01_unique_default_constraint(self):
        """Test constraint: only one default chat model per provider."""
        self.model.default = True
        with self.assertRaises(ValidationError):
            self.env['ai.model'].create({
                'name': 'another-model',
                'provider_id': self.provider.id,
                'model_use': 'chat',
                'default': True,
            })

    def test_02_chat_delegation(self):
        """Test chat delegation to provider."""
        with patch('odoo.addons.odoo_mcp_manager.models.ai_provider.AiProvider.chat') as mocked_chat:
            mocked_chat.return_value = "Hello"
            res = self.model.chat([{'role': 'user', 'content': 'hi'}])
            self.assertEqual(res, "Hello")
            mocked_chat.assert_called_once()

    def test_03_embedding_delegation(self):
        """Test embedding delegation to provider."""
        with patch('odoo.addons.odoo_mcp_manager.models.ai_provider.AiProvider.embedding') as mocked_emb:
            mocked_emb.return_value = [0.1, 0.2]
            res = self.model.embedding("test text")
            self.assertEqual(res, [0.1, 0.2])
            mocked_emb.assert_called_once()
