# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration import ZoomMeetAuth
import odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration as controller_module


@tagged('post_install', '-at_install')
class TestZoomMeetAuth(TransactionCase):

    def setUp(self):
        super(TestZoomMeetAuth, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Zoom Test Company',
            'zoom_client': 'client_id',
            'zoom_client_secret': 'client_secret',
            'zoom_redirect_uri': 'http://localhost/redirect',
        })
        self.controller = ZoomMeetAuth()

    @patch('odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration.requests.post')
    def test_get_auth_code_success(self, mock_post):
        """Test getting authorization code successfully."""
        old_request = controller_module.request
        old_http_request = controller_module.http.request
        mock_request = MagicMock()
        mock_http_request = MagicMock()
        controller_module.request = mock_request
        controller_module.http.request = mock_http_request
        try:
            mock_request.uid = self.env.user.id
            
            mock_env = MagicMock()
            mock_user = MagicMock()
            mock_user.company_id = self.company
            mock_env['res.users'].sudo().browse.return_value = mock_user
            mock_http_request.env = mock_env

            mock_response = MagicMock()
            mock_response.json.return_value = {
                'access_token': 'new_access_token',
                'expires_in': 3600,
                'refresh_token': 'new_refresh_token',
            }
            mock_post.return_value = mock_response

            result = self.controller.get_auth_code(code='auth_code_123')

            self.assertEqual(result.get_data(as_text=True), "Authentication Success. You Can Close this window")
            self.assertEqual(self.company.zoom_company_authorization_code, 'auth_code_123')
            self.assertEqual(self.company.zoom_company_access_token, 'new_access_token')
            self.assertEqual(self.company.zoom_company_refresh_token, 'new_refresh_token')
        finally:
            controller_module.request = old_request
            controller_module.http.request = old_http_request

    @patch('odoo.addons.odoo_zoom_meet_integration.controller.odoo_zoom_meet_integration.requests.post')
    def test_get_auth_code_failure(self, mock_post):
        """Test getting authorization code failure raises error."""
        old_request = controller_module.request
        old_http_request = controller_module.http.request
        mock_request = MagicMock()
        mock_http_request = MagicMock()
        controller_module.request = mock_request
        controller_module.http.request = mock_http_request
        try:
            mock_request.uid = self.env.user.id
            
            mock_env = MagicMock()
            mock_user = MagicMock()
            mock_user.company_id = self.company
            mock_env['res.users'].sudo().browse.return_value = mock_user
            mock_http_request.env = mock_env

            mock_response = MagicMock()
            mock_response.json.return_value = {} # Missing access_token
            mock_post.return_value = mock_response

            with self.assertRaises(UserError):
                self.controller.get_auth_code(code='auth_code_123')
        finally:
            controller_module.request = old_request
            controller_module.http.request = old_http_request
