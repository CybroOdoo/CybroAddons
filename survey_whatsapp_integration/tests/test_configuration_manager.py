# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestConfigurationManager(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_manager = cls.env['configuration.manager'].create({
            'instance': 'instance_123',
            'token': 'token_abc',
            'state': 'draft',
        })

    def test_01_action_authenticate_unauthorized(self):
        """Test action_authenticate with invalid credentials/unauthorized."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 401
            with self.assertRaises(ValidationError) as ctx:
                self.config_manager.action_authenticate()
            self.assertIn("Please provide valid token", str(ctx.exception))

    def test_02_action_authenticate_client_not_found(self):
        """Test action_authenticate when client is not found."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = 'Client not found.'

            res = self.config_manager.action_authenticate()
            self.assertEqual(res['type'], 'ir.actions.client')
            self.assertEqual(res['tag'], 'display_notification')
            self.assertEqual(res['params']['type'], 'danger')
            self.assertEqual(res['params']['message'], 'Please check the field values')

    def test_03_action_authenticate_qr(self):
        """Test action_authenticate returning QR code wizard."""
        mock_response_data = {
            'qr': 'data:image/png;base64,mockbase64qrdata'
        }
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = 'ok'
            mock_get.return_value.json.return_value = mock_response_data

            res = self.config_manager.action_authenticate()
            self.assertEqual(self.config_manager.state, 'draft')
            self.assertEqual(res['type'], 'ir.actions.act_window')
            self.assertEqual(res['res_model'], 'whatsapp.authenticate')
            self.assertEqual(res['context']['default_qrcode'], 'mockbase64qrdata')
            self.assertEqual(res['context']['default_config_manager_id'], self.config_manager.id)

    def test_04_action_authenticate_already_connected(self):
        """Test action_authenticate when already connected."""
        mock_response_data = {
            'is_connected': True
        }
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = 'ok'
            mock_get.return_value.json.return_value = mock_response_data

            res = self.config_manager.action_authenticate()
            self.assertEqual(self.config_manager.state, 'verified')
            self.assertEqual(res['type'], 'ir.actions.client')
            self.assertEqual(res['tag'], 'display_notification')
            self.assertEqual(res['params']['type'], 'success')
            self.assertEqual(res['params']['message'], 'Already connected')

    def test_05_display_notification(self):
        """Test display_notification directly."""
        res = self.config_manager.display_notification('info', 'My Message')
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['tag'], 'display_notification')
        self.assertEqual(res['params']['message'], 'My Message')
        self.assertEqual(res['params']['type'], 'info')

    def test_06_open_authenticate_wizard(self):
        """Test open_authenticate_wizard directly."""
        res = self.config_manager.open_authenticate_wizard('qrcode_data')
        self.assertEqual(res['type'], 'ir.actions.act_window')
        self.assertEqual(res['res_model'], 'whatsapp.authenticate')
        self.assertEqual(res['context']['default_qrcode'], 'qrcode_data')
        self.assertEqual(res['context']['default_config_manager_id'], self.config_manager.id)
