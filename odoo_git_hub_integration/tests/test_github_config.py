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
import requests
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from unittest.mock import patch

class TestGithubConfig(TransactionCase):
    """
    Test suite for the github.config model to verify connection testing functionality.
    """

    def setUp(self):
        """
        Set up the test environment by creating a mock GitHub configuration record.
        """
        super(TestGithubConfig, self).setUp()
        self.github_config = self.env['github.config'].create({
            'name': 'Test GitHub Config',
            'access_token': 'dummy_token',
            'username': 'dummy_user'
        })

    @patch('requests.get')
    def test_01_action_test_connection_success(self, mock_get):
        """
        Test that a successful API response correctly validates the connection
        and matches the configured username.
        """
        # Mock successful response
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {'login': 'dummy_user'}
        mock_get.return_value = mock_response

        res = self.github_config.action_test_connection()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['tag'], 'display_notification')
        self.assertEqual(res['params']['type'], 'success')
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_02_action_test_connection_username_mismatch(self, mock_get):
        """
        Test that a UserError is raised when the GitHub token is valid but
        belongs to a different user than the one configured.
        """
        # Mock successful response but different user
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {'login': 'different_user'}
        mock_get.return_value = mock_response

        with self.assertRaises(UserError) as e:
            self.github_config.action_test_connection()
            
        self.assertIn("Token is valid, but belongs to user 'different_user', not 'dummy_user'", str(e.exception))
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_03_action_test_connection_failure(self, mock_get):
        """
        Test that a UserError is raised with the specific error message when
        the GitHub API returns an authentication failure or error.
        """
        # Mock failed response
        mock_get.side_effect = requests.exceptions.HTTPError('401 Client Error: Unauthorized')
        
        with self.assertRaises(UserError) as e:
            self.github_config.action_test_connection()
            
        self.assertIn("Connection failed: 401 Client Error: Unauthorized", str(e.exception))
        mock_get.assert_called_once()
