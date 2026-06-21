# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install')
class TestResCompanyZoom(TransactionCase):

    def setUp(self):
        super(TestResCompanyZoom, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Zoom Test Company',
        })

    def test_action_zoom_meet_company_authenticate_no_client(self):
        """Test authenticate raises error if no client ID."""
        with self.assertRaises(ValidationError):
            self.company.action_zoom_meet_company_authenticate()

    def test_action_zoom_meet_company_authenticate_no_redirect(self):
        """Test authenticate raises error if no redirect URI."""
        self.company.zoom_client = 'test_client'
        self.company.zoom_redirect_uri = False
        with self.assertRaises(ValidationError):
            self.company.action_zoom_meet_company_authenticate()

    def test_action_zoom_meet_company_authenticate_success(self):
        """Test authenticate returns correct URL action."""
        self.company.zoom_client = 'test_client'
        self.company.zoom_redirect_uri = 'http://localhost'
        result = self.company.action_zoom_meet_company_authenticate()
        
        self.assertEqual(result.get('type'), 'ir.actions.act_url')
        self.assertIn('client_id=test_client', result.get('url'))
        self.assertIn('redirect_uri=http://localhost', result.get('url'))

    def test_action_zoom_meet_company_refresh_token_no_client(self):
        """Test refresh token raises error if no client ID."""
        with self.assertRaises(UserError):
            self.company.action_zoom_meet_company_refresh_token()

    def test_action_zoom_meet_company_refresh_token_no_secret(self):
        """Test refresh token raises error if no client secret."""
        self.company.zoom_client = 'test_client'
        with self.assertRaises(UserError):
            self.company.action_zoom_meet_company_refresh_token()

    def test_action_zoom_meet_company_refresh_token_no_refresh(self):
        """Test refresh token raises error if no refresh token."""
        self.company.zoom_client = 'test_client'
        self.company.zoom_client_secret = 'test_secret'
        with self.assertRaises(UserError):
            self.company.action_zoom_meet_company_refresh_token()

    @patch('odoo.addons.odoo_zoom_meet_integration.models.res_company.requests.post')
    def test_action_zoom_meet_company_refresh_token_success(self, mock_post):
        """Test refresh token success sets access token."""
        self.company.write({
            'zoom_client': 'test_client',
            'zoom_client_secret': 'test_secret',
            'zoom_company_refresh_token': 'old_refresh_token'
        })
        
        mock_response = MagicMock()
        mock_response.json.return_value = {'access_token': 'new_access_token'}
        mock_post.return_value = mock_response

        self.company.action_zoom_meet_company_refresh_token()
        self.assertEqual(self.company.zoom_company_access_token, 'new_access_token')

    @patch('odoo.addons.odoo_zoom_meet_integration.models.res_company.requests.post')
    def test_action_zoom_meet_company_refresh_token_failure(self, mock_post):
        """Test refresh token failure raises error."""
        self.company.write({
            'zoom_client': 'test_client',
            'zoom_client_secret': 'test_secret',
            'zoom_company_refresh_token': 'old_refresh_token'
        })
        
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        with self.assertRaises(UserError):
            self.company.action_zoom_meet_company_refresh_token()
