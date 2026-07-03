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

import requests
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestAiProvider(TransactionCase):

    def setUp(self):
        super(TestAiProvider, self).setUp()
        self.provider = self.env['ai.provider'].create({
            'name': 'Test OpenAI',
            'service': 'openai',
            'api_key': 'test-key',
        })

    def test_01_compute_setup_guide(self):
        """Test if the setup guide is correctly computed based on the service."""
        self.provider.service = 'openai'
        self.assertIn('OpenAI Provider Setup', self.provider.setup_guide)
        self.provider.service = 'anthropic'
        self.assertIn('Anthropic Provider Setup', self.provider.setup_guide)

    def test_02_action_fetch_models(self):
        """Test action_fetch_models returns the correct action."""
        action = self.provider.action_fetch_models()
        self.assertEqual(action['res_model'], 'ai.fetch.model.wizard')
        self.assertEqual(action['context']['default_provider_id'], self.provider.id)

    @patch('requests.get')
    def test_03_check_connection_success(self, mock_get):
        """Test successful connection check."""
        mock_get.return_value.status_code = 200
        ok, err = self.provider.check_connection()
        self.assertTrue(ok)
        self.assertEqual(self.provider.connection_status, 'connected')

    @patch('requests.get')
    def test_04_check_connection_failure(self, mock_get):
        """Test failed connection check."""
        mock_get.return_value.status_code = 401
        mock_get.return_value.text = 'Unauthorized'
        ok, err = self.provider.check_connection()
        self.assertFalse(ok)
        self.assertEqual(self.provider.connection_status, 'error')
        self.assertIn('HTTP 401', self.provider.connection_error)

    @patch('requests.get')
    def test_05_fetch_available_models(self, mock_get):
        """Test fetching models from OpenAI."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'data': [
                {'id': 'gpt-4o'},
                {'id': 'text-embedding-3-small'},
            ]
        }
        models_list = self.provider.fetch_available_models()
        self.assertEqual(len(models_list), 2)
        self.assertEqual(models_list[0]['name'], 'gpt-4o')
        self.assertEqual(models_list[0]['model_use'], 'chat')
        self.assertEqual(models_list[1]['name'], 'text-embedding-3-small')
        self.assertEqual(models_list[1]['model_use'], 'embedding')
