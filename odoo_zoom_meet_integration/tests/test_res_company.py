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
from datetime import datetime, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):
    """Test res.company Zoom configuration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def test_zoom_fields_default_empty(self):
        """Test Zoom config fields are empty by default."""
        new_company = self.env['res.company'].create({
            'name': 'Zoom Test Company',
        })

        self.assertFalse(
            new_company.zoom_client,
            "zoom_client should be empty by default."
        )

        self.assertFalse(
            new_company.zoom_client_secret,
            "zoom_client_secret should be empty by default."
        )

        self.assertFalse(
            new_company.zoom_company_access_token,
            "zoom_company_access_token should be empty by default."
        )

        self.assertFalse(
            new_company.zoom_company_refresh_token,
            "zoom_company_refresh_token should be empty by default."
        )

    def test_zoom_redirect_uri_default(self):
        """Test redirect URI has a default value."""
        new_company = self.env['res.company'].create({
            'name': 'Redirect URI Test Company',
        })

        self.assertTrue(
            new_company.zoom_redirect_uri,
            "zoom_redirect_uri should have a default value."
        )

        self.assertIn(
            '/zoom_meet_authentication',
            new_company.zoom_redirect_uri,
            "Redirect URI should end with /zoom_meet_authentication."
        )

    def test_authenticate_no_client_id(self):
        """Test authentication raises error without client ID."""
        self.company.write({
            'zoom_client': False,
            'zoom_redirect_uri': 'http://localhost/zoom_meet_authentication',
        })

        with self.assertRaises(ValidationError):
            self.company.action_zoom_meet_company_authenticate()

    def test_authenticate_returns_url_action(self):
        """Test authentication returns a URL action to Zoom OAuth."""
        self.company.write({
            'zoom_client': 'test_client_123',
            'zoom_redirect_uri': 'http://localhost/zoom_meet_authentication',
        })

        action = self.company.action_zoom_meet_company_authenticate()

        self.assertEqual(
            action['type'],
            'ir.actions.act_url',
            "Action type should be ir.actions.act_url."
        )

        self.assertIn(
            'zoom.us/oauth/authorize',
            action['url'],
            "URL should point to Zoom OAuth authorize endpoint."
        )

        self.assertIn(
            'test_client_123',
            action['url'],
            "URL should contain the client ID."
        )

    def test_refresh_token_no_client_id(self):
        """Test refresh token raises error without client ID."""
        self.company.write({
            'zoom_client': False,
            'zoom_client_secret': 'secret',
            'zoom_company_refresh_token': 'refresh_tok',
        })

        with self.assertRaises(UserError):
            self.company.action_zoom_meet_company_refresh_token()

    def test_refresh_token_no_client_secret(self):
        """Test refresh token raises error without client secret."""
        self.company.write({
            'zoom_client': 'client_123',
            'zoom_client_secret': False,
            'zoom_company_refresh_token': 'refresh_tok',
        })

        with self.assertRaises(UserError):
            self.company.action_zoom_meet_company_refresh_token()

    def test_refresh_token_no_refresh_token(self):
        """Test refresh token raises error without existing refresh token."""
        self.company.write({
            'zoom_client': 'client_123',
            'zoom_client_secret': 'secret_456',
            'zoom_company_refresh_token': False,
        })

        with self.assertRaises(UserError):
            self.company.action_zoom_meet_company_refresh_token()

    @patch(
        'odoo.addons.odoo_zoom_meet_integration.models.'
        'calendar_event.requests.request'
    )
    @patch(
        'odoo.addons.odoo_zoom_meet_integration.models.'
        'calendar_event.requests.delete'
    )
    def test_unlink_zoom_event(self, mock_delete, mock_request):
        """Test unlinking a Zoom event calls the Zoom delete API."""

        mock_create_response = MagicMock()
        mock_create_response.json.return_value = {
            'id': '77777777777',
            'join_url': 'https://zoom.us/j/77777777777',
            'start_url': 'https://zoom.us/s/77777777777',
        }

        mock_request.return_value = mock_create_response
        mock_delete.return_value = MagicMock(status_code=204)

        event = self.env['calendar.event'].create({
            'name': 'Unlink Zoom Test',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
            'is_zoom_meet': True,
        })

        event.unlink()

        mock_request.assert_called_once()
        mock_delete.assert_called_once()

    @patch('odoo.addons.odoo_zoom_meet_integration.models'
           '.res_company.requests.post')
    def test_refresh_token_failure(self, mock_post):
        """Test failed token refresh raises UserError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'error': 'invalid_grant'}
        mock_post.return_value = mock_response

        self.company.write({
            'zoom_client': 'client_123',
            'zoom_client_secret': 'secret_456',
            'zoom_company_refresh_token': 'bad_refresh_token',
        })

        with self.assertRaises(UserError):
            self.company.action_zoom_meet_company_refresh_token()

    def test_write_zoom_credentials(self):
        """Test writing Zoom credentials to company record."""
        self.company.write({
            'zoom_client': 'written_client_id',
            'zoom_client_secret': 'written_client_secret',
            'zoom_company_access_token': 'written_access_token',
            'zoom_company_refresh_token': 'written_refresh_token',
        })

        self.assertEqual(
            self.company.zoom_client,
            'written_client_id',
            "zoom_client should be updated."
        )

        self.assertEqual(
            self.company.zoom_client_secret,
            'written_client_secret',
            "zoom_client_secret should be updated."
        )

        self.assertEqual(
            self.company.zoom_company_access_token,
            'written_access_token',
            "zoom_company_access_token should be updated."
        )

        self.assertEqual(
            self.company.zoom_company_refresh_token,
            'written_refresh_token',
            "zoom_company_refresh_token should be updated."
        )
