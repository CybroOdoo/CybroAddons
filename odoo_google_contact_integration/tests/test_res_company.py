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
from odoo.exceptions import UserError, ValidationError


class MockRequest:
    def __init__(self, env):
        self.env = env


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.user.company_id
        cls.country_us = cls.env['res.country'].search([('code', '=', 'US')], limit=1)
        if not cls.country_us:
            cls.country_us = cls.env['res.country'].create({
                'name': 'United States',
                'code': 'US',
            })
        cls.state_ny = cls.env['res.country.state'].search([('code', '=', 'NY')], limit=1)
        if not cls.state_ny:
            cls.state_ny = cls.env['res.country.state'].create({
                'name': 'New York',
                'code': 'NY',
                'country_id': cls.country_us.id,
            })

    def test_01_compute_contact_redirect_uri(self):
        """Test _compute_contact_redirect_uri handles request context safely."""
        with patch('odoo.addons.odoo_google_contact_integration.models.res_company.request', MockRequest(self.env)):
            self.company._compute_contact_redirect_uri()
            self.assertTrue(self.company.contact_redirect_uri)
            self.assertIn('/google_contact_authentication', self.company.contact_redirect_uri)

    def test_02_action_google_contact_authenticate_validation(self):
        """Test action_google_contact_authenticate validation constraints."""
        self.company.write({
            'contact_client_id': False,
        })
        with patch('odoo.addons.odoo_google_contact_integration.models.res_company.request', MockRequest(self.env)):
            with self.assertRaises(ValidationError) as ctx:
                self.company.action_google_contact_authenticate()
            self.assertIn("Please Enter Client ID", str(ctx.exception))

            self.company.contact_client_id = 'client_123'
            with patch.object(type(self.company), 'contact_redirect_uri', new=False):
                with self.assertRaises(ValidationError) as ctx2:
                    self.company.action_google_contact_authenticate()
                self.assertIn("Please Enter Redirect URL", str(ctx2.exception))

    def test_03_action_google_contact_authenticate_success(self):
        """Test action_google_contact_authenticate returns action dict."""
        self.company.contact_client_id = 'client_123'
        with patch('odoo.addons.odoo_google_contact_integration.models.res_company.request', MockRequest(self.env)):
            res = self.company.action_google_contact_authenticate()
            self.assertEqual(res['type'], 'ir.actions.act_url')
            self.assertEqual(res['target'], 'new')
            self.assertIn('https://accounts.google.com/o/oauth2/v2/auth', res['url'])

    def test_04_action_google_contact_refresh_token_validation(self):
        """Test action_google_contact_refresh_token missing configurations."""
        self.company.write({
            'contact_client_id': False,
            'contact_client_secret': False,
            'contact_company_refresh_token': False,
        })

        with self.assertRaises(UserError) as ctx:
            self.company.action_google_contact_refresh_token()
        self.assertIn("Client ID is not yet configured", str(ctx.exception))

        self.company.contact_client_id = 'client_123'
        with self.assertRaises(UserError) as ctx2:
            self.company.action_google_contact_refresh_token()
        self.assertIn("Client Secret is not yet configured", str(ctx2.exception))

        self.company.contact_client_secret = 'secret_abc'
        with self.assertRaises(UserError) as ctx3:
            self.company.action_google_contact_refresh_token()
        self.assertIn("Refresh Token is not yet configured", str(ctx3.exception))

    def test_05_action_google_contact_refresh_token_success(self):
        """Test action_google_contact_refresh_token successfully retrieves and stores access token."""
        self.company.write({
            'contact_client_id': 'client_123',
            'contact_client_secret': 'secret_abc',
            'contact_company_refresh_token': 'refresh_xyz',
        })

        mock_response = {
            'access_token': 'new_access_token_123',
        }
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            self.company.action_google_contact_refresh_token()
            self.assertEqual(self.company.contact_company_access_token, 'new_access_token_123')

    def test_06_action_google_contact_refresh_token_failure(self):
        """Test action_google_contact_refresh_token handles response errors correctly."""
        self.company.write({
            'contact_client_id': 'client_123',
            'contact_client_secret': 'secret_abc',
            'contact_company_refresh_token': 'refresh_xyz',
        })

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {'error': 'invalid_grant'}

            with self.assertRaises(UserError) as ctx:
                self.company.action_google_contact_refresh_token()
            self.assertIn("Something went wrong during the token generation", str(ctx.exception))

    def test_07_action_import_google_contacts_api_error(self):
        """Test action_import_google_contacts handles API status error."""
        self.company.contact_company_access_token = 'token_123'
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 401
            mock_get.return_value.text = 'Unauthorized'

            with self.assertRaises(ValidationError) as ctx:
                self.company.action_import_google_contacts()
            self.assertIn("Failed to import contact", str(ctx.exception))

    def test_08_action_import_google_contacts_success(self):
        """Test importing contacts from Google creates or updates partners."""
        self.company.contact_company_access_token = 'token_123'
        mock_response_data = {
            'connections': [
                {
                    'resourceName': 'people/c123456789',
                    'etag': 'version1',
                    'names': [
                        {
                            'givenName': 'John',
                            'familyName': 'Doe',
                            'displayName': 'John Doe',
                        }
                    ],
                    'emailAddresses': [
                        {
                            'value': 'john.doe@example.com',
                        }
                    ],
                    'phoneNumbers': [
                        {
                            'value': '+1234567890',
                        }
                    ],
                    'addresses': [
                        {
                            'streetAddress': '123 Main St',
                            'extendedAddress': 'Apt 4B',
                            'city': 'New York',
                            'postalCode': '10001',
                            'region': 'New York',
                            'countryCode': 'US',
                        }
                    ]
                }
            ],
            'nextPageToken': False,
        }

        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response_data

            res = self.company.action_import_google_contacts()
            self.assertEqual(res['type'], 'ir.actions.client')
            self.assertEqual(res['tag'], 'display_notification')
            self.assertEqual(res['params']['type'], 'success')

            partner = self.env['res.partner'].search([('google_resource', '=', 'people/c123456789')], limit=1)
            self.assertTrue(partner)
            self.assertEqual(partner.name, 'John Doe')
            self.assertEqual(partner.first_name, 'John')
            self.assertEqual(partner.last_name, 'Doe')
            self.assertEqual(partner.email, 'john.doe@example.com')
            self.assertEqual(partner.phone, '+1234567890')
            self.assertEqual(partner.street, '123 Main St')
            self.assertEqual(partner.street2, 'Apt 4B')
            self.assertEqual(partner.city, 'New York')
            self.assertEqual(partner.zip, '10001')
            self.assertEqual(partner.state_id, self.state_ny)
            self.assertEqual(partner.country_id, self.country_us)
            self.assertEqual(partner.google_etag, 'version1')

            mock_response_data['connections'][0]['names'][0]['displayName'] = 'John Doe Updated'
            mock_response_data['connections'][0]['etag'] = 'version2'
            self.company.action_import_google_contacts()

            partner_updated = self.env['res.partner'].search([('google_resource', '=', 'people/c123456789')], limit=1)
            self.assertEqual(partner_updated.name, 'John Doe Updated')
            self.assertEqual(partner_updated.google_etag, 'version2')
