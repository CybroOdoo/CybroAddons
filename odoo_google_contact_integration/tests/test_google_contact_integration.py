# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from odoo.addons.odoo_google_contact_integration.controllers.google_contact_integration import GoogleContactAuth


class MockRequest:
    def __init__(self, uid, env):
        self.uid = uid
        self.env = env


@tagged('post_install', '-at_install')
class TestGoogleContactIntegration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = cls.env['res.users'].search([('company_id', '!=', False)], limit=1)
        cls.company = user.company_id
        cls.company.write({
            'contact_client_id': 'client_123',
            'contact_client_secret': 'secret_abc',
        })
        cls.controller = GoogleContactAuth()
        cls.mock_request = MockRequest(user.id, cls.env)

    def test_01_get_auth_code_no_code(self):
        """Test get_auth_code when no code is passed in parameters."""
        with patch('odoo.addons.odoo_google_contact_integration.controllers.google_contact_integration.request', self.mock_request), \
             patch('odoo.addons.odoo_google_contact_integration.controllers.google_contact_integration.http.request', self.mock_request), \
             patch('odoo.addons.odoo_google_contact_integration.models.res_company.request', self.mock_request):
            res = self.controller.get_auth_code()
            self.assertEqual(res.data, b'')

    def test_02_get_auth_code_success(self):
        """Test get_auth_code processes code and fetches token successfully."""
        mock_response = {
            'access_token': 'access_token_xyz',
            'expires_in': 3600,
        }
        with patch('odoo.addons.odoo_google_contact_integration.controllers.google_contact_integration.request', self.mock_request), \
             patch('odoo.addons.odoo_google_contact_integration.controllers.google_contact_integration.http.request', self.mock_request), \
             patch('odoo.addons.odoo_google_contact_integration.models.res_company.request', self.mock_request), \
             patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            res = self.controller.get_auth_code(code='auth_code_789')
            self.company.invalidate_recordset()
            self.assertEqual(res.data, b"Authentication Success. You Can Close this window")
            self.assertEqual(self.company.contact_company_authorization_code, 'auth_code_789')
            self.assertEqual(self.company.contact_company_access_token, 'access_token_xyz')
            self.assertEqual(self.company.contact_company_refresh_token, 'access_token_xyz')
            self.assertTrue(self.company.contact_company_access_token_expiry)

    def test_03_get_auth_code_failure(self):
        """Test get_auth_code raises UserError when token endpoint fails."""
        with patch('odoo.addons.odoo_google_contact_integration.controllers.google_contact_integration.request', self.mock_request), \
             patch('odoo.addons.odoo_google_contact_integration.controllers.google_contact_integration.http.request', self.mock_request), \
             patch('odoo.addons.odoo_google_contact_integration.models.res_company.request', self.mock_request), \
             patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {'error': 'invalid_grant'}

            with self.assertRaises(UserError) as ctx:
                self.controller.get_auth_code(code='invalid_code')
            self.assertIn("Something went wrong during the token generation", str(ctx.exception))
