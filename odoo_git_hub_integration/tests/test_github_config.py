# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################

from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestGitHubConfig(TransactionCase):
    """Test cases for the GitHubConfig model (github.config)."""

    def setUp(self):
        super().setUp()
        self.config = self.env['github.config'].create({
            'name': 'Test GitHub Config',
            'access_token': 'test_fake_token_12345',
            'username': 'testuser',
        })

    def test_config_creation(self):
        """Test that a github.config record can be created."""
        self.assertTrue(self.config.id, "Config record should be created.")
        self.assertEqual(self.config.name, 'Test GitHub Config')
        self.assertEqual(self.config.username, 'testuser')

    def test_config_default_active(self):
        """Test that a new config is active by default."""
        self.assertTrue(self.config.active, "Config should be active by default.")

    def test_action_test_connection_success(self):
        """Test action_test_connection with a successful API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'login': 'testuser'}
        mock_response.raise_for_status = MagicMock()

        with patch('requests.get', return_value=mock_response):
            result = self.config.action_test_connection()

        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['type'], 'success')

    def test_action_test_connection_wrong_user(self):
        """Test action_test_connection raises UserError when token belongs to wrong user."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'login': 'differentuser'}
        mock_response.raise_for_status = MagicMock()

        with patch('requests.get', return_value=mock_response):
            with self.assertRaises(UserError):
                self.config.action_test_connection()

    def test_action_test_connection_failure(self):
        """Test action_test_connection raises UserError when request fails."""
        with patch('requests.get', side_effect=Exception("Connection refused")):
            with self.assertRaises(UserError):
                self.config.action_test_connection()
