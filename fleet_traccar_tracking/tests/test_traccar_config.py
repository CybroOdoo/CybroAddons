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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

class TestTraccarConfig(TransactionCase):

    def setUp(self):
        super(TestTraccarConfig, self).setUp()
        self.Config = self.env['fleet.traccar.config']
        # Clean up any existing config
        self.Config.search([]).unlink()
        self.config = self.Config.create({
            'name': 'Test Config',
            'traccar_url': 'http://test.traccar.com',
            'traccar_username': 'user',
            'traccar_password': 'pass',
        })

    def test_get_config(self):
        """Test singleton behavior of get_config."""
        config = self.env['fleet.traccar.config'].get_config()
        self.assertEqual(config, self.config)

    def test_copy_raises_user_error(self):
        """Test that duplicating the config raises a UserError."""
        with self.assertRaises(UserError):
            self.config.copy()

    def test_get_auth(self):
        """Test authentication tuple generation."""
        auth = self.config._get_auth()
        self.assertEqual(auth, ('user', 'pass'))

        self.config.traccar_url = False
        with self.assertRaises(UserError):
            self.config._get_auth()

    @patch('requests.get')
    def test_api_get_success(self, mock_get):
        """Test successful API GET request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'version': '5.0'}
        mock_get.return_value = mock_response

        data = self.config._api_get('/api/server')
        self.assertEqual(data.get('version'), '5.0')
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_api_get_failure(self, mock_get):
        """Test API GET request failure handling."""
        mock_get.side_effect = Exception("Connection Refused")
        
        with self.assertRaises(UserError):
            self.config._api_get('/api/server')

    @patch('requests.get')
    def test_test_connection(self, mock_get):
        """Test the 'Test Connection' action button."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [{'version': '5.0'}, [{'id': 1}]]
        mock_get.return_value = mock_response

        self.config.action_test_connection()
        self.assertIn('Connected', self.config.connection_status)

    @patch('requests.get')
    def test_sync_devices(self, mock_get):
        """Test importing devices from Traccar API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'name': 'Device 1', 'uniqueId': '123'},
            {'id': 2, 'name': 'Device 2', 'uniqueId': '456'},
        ]
        mock_get.return_value = mock_response

        self.config.action_sync_devices()
        
        device1 = self.env['fleet.traccar.device'].search([('traccar_id', '=', 1)])
        self.assertTrue(device1)
        self.assertEqual(device1.name, 'Device 1')
        self.assertEqual(device1.unique_id, '123')

        device2 = self.env['fleet.traccar.device'].search([('traccar_id', '=', 2)])
        self.assertTrue(device2)
