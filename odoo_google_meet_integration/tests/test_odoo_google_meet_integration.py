# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from odoo.addons.odoo_google_meet_integration.controllers.odoo_google_meet_integration import GoogleMeetAuth


class MockRequest:
    def __init__(self, uid, env):
        self.uid = uid
        self.env = env


@tagged('post_install', '-at_install')
class TestOdooGoogleMeetIntegration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Fetch user with company
        user = cls.env['res.users'].search([('company_id', '!=', False)], limit=1)
        cls.company = user.company_id
        cls.company.write({
            'hangout_client_id': 'client_123',
            'hangout_client_secret': 'secret_abc',
            'hangout_redirect_uri': 'http://localhost:8069/google_meet_authentication',
        })
        cls.controller = GoogleMeetAuth()
        cls.mock_request = MockRequest(user.id, cls.env)

    def test_01_get_auth_code_no_code(self):
        """Test get_auth_code when code is not present in parameters."""
        with patch('odoo.addons.odoo_google_meet_integration.controllers.odoo_google_meet_integration.request',
                   self.mock_request), \
                patch('odoo.addons.odoo_google_meet_integration.controllers.odoo_google_meet_integration.http.request',
                      self.mock_request):
            res = self.controller.get_auth_code()
            self.assertEqual(res.data, b'')

    def test_02_get_auth_code_success(self):
        """Test get_auth_code successfully processes code and gets access token."""
        mock_response = {
            'access_token': 'meet_access_token_xyz',
            'expires_in': 3600,
        }

        with patch('odoo.addons.odoo_google_meet_integration.controllers.odoo_google_meet_integration.request',
                   self.mock_request), \
                patch('odoo.addons.odoo_google_meet_integration.controllers.odoo_google_meet_integration.http.request',
                      self.mock_request), \
                patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            res = self.controller.get_auth_code(code='auth_code_meet_123')
            self.company.invalidate_recordset()

            self.assertEqual(res.data, b"Authentication Success. You Can Close this window")
            self.assertEqual(self.company.hangout_company_authorization_code, 'auth_code_meet_123')
            self.assertEqual(self.company.hangout_company_access_token, 'meet_access_token_xyz')
            self.assertEqual(self.company.hangout_company_refresh_token, 'meet_access_token_xyz')
            self.assertTrue(self.company.hangout_company_access_token_expiry)

    def test_03_get_auth_code_failure(self):
        """Test get_auth_code raises UserError when token API call fails."""
        with patch('odoo.addons.odoo_google_meet_integration.controllers.odoo_google_meet_integration.request',
                   self.mock_request), \
                patch('odoo.addons.odoo_google_meet_integration.controllers.odoo_google_meet_integration.http.request',
                      self.mock_request), \
                patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {'error': 'invalid_grant'}

            with self.assertRaises(UserError) as ctx:
                self.controller.get_auth_code(code='invalid_code')
            self.assertIn("Something went wrong during the token generation", str(ctx.exception))
