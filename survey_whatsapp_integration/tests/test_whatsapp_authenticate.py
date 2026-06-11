# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch, MagicMock
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestWhatsappAuthenticate(TransactionCase):
    """Test cases for the Whatsapp Authentication wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_manager = cls.env['configuration.manager'].create({
            'instance': 'test_instance',
            'token': 'test_token'
        })
        cls.wizard = cls.env['whatsapp.authenticate'].create({
            'configuration_manager_id': cls.config_manager.id
        })

    @patch('odoo.addons.survey_whatsapp_integration.wizard.whatsapp_authenticate.requests.get')
    def test_check_active_connected(self, mock_get):
        """Test _check_active when whatsapp is connected."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'is_connected': True}
        mock_get.return_value = mock_response

        result = self.wizard._check_active()

        self.assertEqual(self.config_manager.state, 'verified')
        self.assertIsNone(result)

    @patch('odoo.addons.survey_whatsapp_integration.wizard.whatsapp_authenticate.requests.get')
    def test_check_active_not_connected(self, mock_get):
        """Test _check_active when whatsapp is not connected raises ValidationError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}  # 'is_connected' not in keys
        mock_get.return_value = mock_response

        with self.assertRaises(ValidationError) as cm:
            self.wizard._check_active()
            
        self.assertIn("Please scan and connect your whatsapp web", str(cm.exception))

    @patch('odoo.addons.survey_whatsapp_integration.wizard.whatsapp_authenticate.requests.get')
    def test_check_active_connected_false(self, mock_get):
        """Test _check_active when is_connected is False returns notification."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'is_connected': False}
        mock_get.return_value = mock_response
        self.config_manager.state = 'draft'

        result = self.wizard._check_active()

        self.assertEqual(self.config_manager.state, 'draft')
        self.assertIsNotNone(result)
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'display_notification')
        self.assertEqual(result['params']['type'], 'danger')