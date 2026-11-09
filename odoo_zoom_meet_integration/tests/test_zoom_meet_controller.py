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

from odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration import (
    ZoomMeetAuth,
)
from odoo.exceptions import UserError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestZoomMeetController(common.TransactionCase):
    """Unit test suite for ZoomMeetAuth controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'zoom_client': 'zoom_test_client_id',
            'zoom_client_secret': 'zoom_test_client_secret',
            'zoom_redirect_uri': 'http://localhost:8069/zoom_meet_authentication',
        })
        cls.controller = ZoomMeetAuth()

    @patch('odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration.requests.post')
    def test_01_get_auth_code_success(self, mock_post):
        """Test controller exchange of auth code for access token successfully updates company."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'new_ctrl_access_token_xyz',
            'expires_in': 7200,
            'refresh_token': 'new_ctrl_refresh_token_xyz',
            'token_type': 'bearer',
        }
        mock_post.return_value = mock_response

        mock_request = MagicMock()
        mock_request.uid = self.env.user.id
        mock_request.env = self.env

        with patch(
            'odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration.request',
            mock_request,
        ), patch(
            'odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration.http.request',
            mock_request,
        ):
            result = self.controller.get_auth_code(code='test_oauth_code_1234')

        data_text = result.get_data(as_text=True) if hasattr(result, 'get_data') else str(result)
        self.assertEqual(data_text, "Authentication Success. You Can Close this window")
        self.assertEqual(self.company.zoom_company_authorization_code, 'test_oauth_code_1234')
        self.assertEqual(self.company.zoom_company_access_token, 'new_ctrl_access_token_xyz')
        self.assertEqual(self.company.zoom_company_refresh_token, 'new_ctrl_refresh_token_xyz')
        self.assertTrue(self.company.zoom_company_access_token_expiry)

    @patch('odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration.requests.post')
    def test_02_get_auth_code_failure(self, mock_post):
        """Test controller raises UserError when token endpoint returns invalid response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'error': 'invalid_request',
            'error_description': 'Invalid authorization code',
        }
        mock_post.return_value = mock_response

        mock_request = MagicMock()
        mock_request.uid = self.env.user.id
        mock_request.env = self.env

        with patch(
            'odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration.request',
            mock_request,
        ), patch(
            'odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration.http.request',
            mock_request,
        ):
            with self.assertRaises(UserError) as cm:
                self.controller.get_auth_code(code='invalid_code')

        self.assertIn("Something went wrong during the token generation.", str(cm.exception))

    def test_03_get_auth_code_no_code(self):
        """Test controller does nothing and returns empty response when code is absent."""
        mock_request = MagicMock()
        mock_request.uid = self.env.user.id
        mock_request.env = self.env

        with patch(
            'odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration.request',
            mock_request,
        ), patch(
            'odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration.http.request',
            mock_request,
        ):
            result = self.controller.get_auth_code()

        data_text = result.get_data(as_text=True) if hasattr(result, 'get_data') else (result or '')
        self.assertEqual(data_text, '')


@tagged('post_install', '-at_install')
class TestZoomMeetControllerHttp(common.HttpCase):
    """Integration test suite for /zoom_meet_authentication endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'zoom_client': 'http_test_client_id',
            'zoom_client_secret': 'http_test_client_secret',
            'zoom_redirect_uri': 'http://localhost:8069/zoom_meet_authentication',
        })

    def test_04_http_endpoint_without_code(self):
        """GET /zoom_meet_authentication without code responds with HTTP 200."""
        response = self.url_open('/zoom_meet_authentication')
        self.assertEqual(response.status_code, 200)

    @patch('odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration.requests.post')
    def test_05_http_endpoint_with_code_success(self, mock_post):
        """GET /zoom_meet_authentication with code returns success message."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'http_test_access_token',
            'expires_in': 3600,
            'refresh_token': 'http_test_refresh_token',
        }
        mock_post.return_value = mock_response

        response = self.url_open('/zoom_meet_authentication?code=mock_http_code')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Authentication Success. You Can Close this window", response.text)
