# -*- coding: utf-8 -*-
#################################################################################
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
################################################################################

from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestResCompanyZoom(common.TransactionCase):
    """Test suite for Zoom Meet configuration on res.company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def test_01_action_zoom_meet_company_authenticate_missing_client_id(self):
        """Test authenticate raises ValidationError if zoom_client is missing."""
        self.company.zoom_client = False
        with self.assertRaises(ValidationError) as cm:
            self.company.action_zoom_meet_company_authenticate()
        self.assertIn("Please Enter Client ID", str(cm.exception))

    def test_02_action_zoom_meet_company_authenticate_missing_redirect_uri(self):
        """Test authenticate raises ValidationError if zoom_redirect_uri is missing."""
        self.company.zoom_client = "client_test_id"
        self.company.zoom_redirect_uri = False
        with self.assertRaises(ValidationError) as cm:
            self.company.action_zoom_meet_company_authenticate()
        self.assertIn("Please Enter Client Secret", str(cm.exception))

    def test_03_action_zoom_meet_company_authenticate_success(self):
        """Test authenticate returns act_url action with correct authorization URL."""
        self.company.zoom_client = "test_client_id_123"
        self.company.zoom_redirect_uri = "https://example.com/zoom_meet_authentication"
        action = self.company.action_zoom_meet_company_authenticate()

        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertEqual(action.get('target'), 'current')
        expected_url = (
            "https://zoom.us/oauth/authorize?response_type=code"
            "&client_id=test_client_id_123&redirect_uri=https://example.com/zoom_meet_authentication"
        )
        self.assertEqual(action.get('url'), expected_url)

    def test_04_action_zoom_meet_company_refresh_token_missing_client_id(self):
        """Test refresh token raises UserError if zoom_client is missing."""
        self.company.zoom_client = False
        with self.assertRaises(UserError) as cm:
            self.company.action_zoom_meet_company_refresh_token()
        self.assertIn("Client ID is not yet configured.", str(cm.exception))

    def test_05_action_zoom_meet_company_refresh_token_missing_client_secret(self):
        """Test refresh token raises UserError if zoom_client_secret is missing."""
        self.company.zoom_client = "test_client_id"
        self.company.zoom_client_secret = False
        with self.assertRaises(UserError) as cm:
            self.company.action_zoom_meet_company_refresh_token()
        self.assertIn("Client Secret is not yet configured.", str(cm.exception))

    def test_06_action_zoom_meet_company_refresh_token_missing_refresh_token(self):
        """Test refresh token raises UserError if zoom_company_refresh_token is missing."""
        self.company.zoom_client = "test_client_id"
        self.company.zoom_client_secret = "test_client_secret"
        self.company.zoom_company_refresh_token = False
        with self.assertRaises(UserError) as cm:
            self.company.action_zoom_meet_company_refresh_token()
        self.assertIn("Refresh Token is not yet configured.", str(cm.exception))

    @patch('odoo.addons.odoo_zoom_meet_integration.models.res_company.requests.post')
    def test_07_action_zoom_meet_company_refresh_token_success(self, mock_post):
        """Test refresh token succeeds and stores new access token on res.company."""
        self.company.write({
            'zoom_client': 'client_123',
            'zoom_client_secret': 'secret_456',
            'zoom_company_refresh_token': 'refresh_old',
        })
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'new_zoom_access_token_999',
            'token_type': 'bearer',
            'expires_in': 3600,
        }
        mock_post.return_value = mock_response

        self.company.action_zoom_meet_company_refresh_token()
        self.assertEqual(self.company.zoom_company_access_token, 'new_zoom_access_token_999')
        mock_post.assert_called_once()

    @patch('odoo.addons.odoo_zoom_meet_integration.models.res_company.requests.post')
    def test_08_action_zoom_meet_company_refresh_token_failure(self, mock_post):
        """Test refresh token raises UserError when Zoom API returns error or no access_token."""
        self.company.write({
            'zoom_client': 'client_123',
            'zoom_client_secret': 'secret_456',
            'zoom_company_refresh_token': 'refresh_invalid',
        })
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'error': 'invalid_grant',
            'error_description': 'Invalid refresh token',
        }
        mock_post.return_value = mock_response

        with self.assertRaises(UserError) as cm:
            self.company.action_zoom_meet_company_refresh_token()
        self.assertIn("Something went wrong during the token generation.", str(cm.exception))

    def test_09_res_company_get_views(self):
        """Verify that res.company form view with inherited Zoom Meet fields renders without error."""
        res = self.env['res.company'].get_views([(False, 'form')])
        self.assertIsInstance(res, dict)
        self.assertIn('views', res)

