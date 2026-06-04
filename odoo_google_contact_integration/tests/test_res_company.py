# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError


def _mock_response(status_code=200, json_data=None, text=''):
    """Build a minimal mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text
    return resp


@tagged('post_install', '-at_install', 'odoo_google_contact_integration')
class TestResCompanyFields(TransactionCase):
    """Field-presence and default tests for res.company extension."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company

    # ------------------------------------------------------------------
    # 1. Field presence & defaults
    # ------------------------------------------------------------------

    def test_required_contact_fields_exist(self):
        required_fields = [
            'contact_client_id',
            'contact_client_secret',
            'contact_redirect_uri',
            'contact_company_access_token',
            'contact_company_refresh_token',
            'contact_company_authorization_code',
            'contact_company_access_token_expiry',
        ]
        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, self.env['res.company']._fields)

    def test_redirect_uri_default(self):
        """contact_redirect_uri must default to the localhost OAuth callback."""
        company = self.env['res.company'].create({
            'name': 'Test Google Co',
            'currency_id': self.env.ref('base.USD').id,
        })
        self.assertIn('google_contact_authentication',
                      company.contact_redirect_uri or '')


@tagged('post_install', '-at_install', 'odoo_google_contact_integration')
class TestResCompanyAuthenticate(TransactionCase):
    """Tests for action_google_contact_authenticate."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company

    def test_authenticate_raises_without_client_id(self):
        """Missing client_id must raise ValidationError."""
        self.company.contact_client_id = False
        with self.assertRaises(ValidationError):
            self.company.action_google_contact_authenticate()

    def test_authenticate_raises_without_redirect_uri(self):
        """Missing redirect_uri must raise ValidationError."""
        self.company.contact_client_id = 'some-client-id'
        self.company.contact_redirect_uri = False
        with self.assertRaises(ValidationError):
            self.company.action_google_contact_authenticate()

    def test_authenticate_returns_act_url(self):
        """With valid client_id and redirect_uri, must return act_url action."""
        self.company.contact_client_id = 'my-client-id'
        self.company.contact_redirect_uri = 'http://localhost:8016/google_contact_authentication'
        result = self.company.action_google_contact_authenticate()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')

    def test_authenticate_url_contains_client_id(self):
        """The returned URL must embed the configured client_id."""
        self.company.contact_client_id = 'unique-client-xyz'
        self.company.contact_redirect_uri = 'http://localhost:8016/cb'
        result = self.company.action_google_contact_authenticate()
        self.assertIn('unique-client-xyz', result.get('url', ''))

    def test_authenticate_url_contains_contacts_scope(self):
        """The returned URL must request the Google Contacts OAuth scope."""
        self.company.contact_client_id = 'cid'
        self.company.contact_redirect_uri = 'http://localhost/cb'
        result = self.company.action_google_contact_authenticate()
        self.assertIn('contacts', result.get('url', ''))

    def test_authenticate_target_new(self):
        """The action must open in a new window (target='new')."""
        self.company.contact_client_id = 'cid'
        self.company.contact_redirect_uri = 'http://localhost/cb'
        result = self.company.action_google_contact_authenticate()
        self.assertEqual(result.get('target'), 'new')


@tagged('post_install', '-at_install', 'odoo_google_contact_integration')
class TestResCompanyRefreshToken(TransactionCase):
    """Tests for action_google_contact_refresh_token."""

    def setUp(self):
        """Set up a company with valid OAuth credentials for each test."""
        super().setUp()
        self.company = self.env.company
        self.company.contact_client_id = 'client-id'
        self.company.contact_client_secret = 'client-secret'
        self.company.contact_company_refresh_token = 'refresh-token'

    def test_refresh_raises_without_client_id(self):
        """Should raise UserError when contact_client_id is not set."""
        self.company.contact_client_id = False
        with self.assertRaises(UserError):
            self.company.action_google_contact_refresh_token()

    def test_refresh_raises_without_client_secret(self):
        """Should raise UserError when contact_client_secret is not set."""
        self.company.contact_client_secret = False
        with self.assertRaises(UserError):
            self.company.action_google_contact_refresh_token()

    def test_refresh_raises_without_refresh_token(self):
        """Should raise UserError when contact_company_refresh_token is not set."""
        self.company.contact_company_refresh_token = False
        with self.assertRaises(UserError):
            self.company.action_google_contact_refresh_token()

    @patch('odoo.addons.odoo_google_contact_integration.models.res_company.requests.post')
    def test_refresh_stores_access_token_on_success(self, mock_post):
        """A 200 response with access_token must update the company record."""
        mock_post.return_value = _mock_response(
            json_data={'access_token': 'new-access-token-abc'})
        self.company.action_google_contact_refresh_token()
        self.assertEqual(self.company.contact_company_access_token,
                         'new-access-token-abc')

    @patch('odoo.addons.odoo_google_contact_integration.models.res_company.requests.post')
    def test_refresh_raises_on_missing_access_token(self, mock_post):
        """Response without access_token must raise UserError."""
        mock_post.return_value = _mock_response(json_data={})
        with self.assertRaises(UserError):
            self.company.action_google_contact_refresh_token()

    @patch('odoo.addons.odoo_google_contact_integration.models.res_company.requests.post')
    def test_refresh_posts_to_correct_url(self, mock_post):
        """Token refresh must POST to Google OAuth token endpoint."""
        mock_post.return_value = _mock_response(
            json_data={'access_token': 'tok'})
        self.company.action_google_contact_refresh_token()
        call_url = mock_post.call_args[0][0]
        self.assertIn('oauth2/token', call_url)


@tagged('post_install', '-at_install', 'odoo_google_contact_integration')
class TestResCompanyImport(TransactionCase):
    """Tests for action_import_google_contacts."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.company.contact_company_access_token = 'valid-access-token'

    def _google_connection(self, first='John', last='Doe',
                           email='john@example.com', phone='+91999',
                           resource='people/c123', etag='abc123',
                           country_code='IN'):
        return {
            'resourceName': resource,
            'etag': etag,
            'names': [{'givenName': first, 'familyName': last,
                       'displayName': f'{first} {last}'}],
            'emailAddresses': [{'value': email}],
            'phoneNumbers': [{'value': phone}],
            'addresses': [{'streetAddress': '123 MG Road',
                           'extendedAddress': 'Floor 2',
                           'city': 'Kochi', 'postalCode': '682001',
                           'region': 'Kerala',
                           'countryCode': country_code}],
        }

    @patch('odoo.addons.odoo_google_contact_integration.models.res_company.requests.get')
    def test_import_creates_new_partner(self, mock_get):
        """A new Google contact must create a new res.partner record."""
        mock_get.return_value = _mock_response(
            json_data={'connections': [self._google_connection()]})
        before = self.env['res.partner'].search_count([])
        self.company.action_import_google_contacts()
        after = self.env['res.partner'].search_count([])
        self.assertGreater(after, before)

    @patch('odoo.addons.odoo_google_contact_integration.models.res_company.requests.get')
    def test_import_sets_google_resource(self, mock_get):
        """Imported partner must have google_resource set from the API response."""
        mock_get.return_value = _mock_response(
            json_data={'connections': [
                self._google_connection(resource='people/c999')]})
        self.company.action_import_google_contacts()
        partner = self.env['res.partner'].search(
            [('google_resource', '=', 'people/c999')], limit=1)
        self.assertTrue(partner)

    @patch('odoo.addons.odoo_google_contact_integration.models.res_company.requests.get')
    def test_import_updates_existing_partner(self, mock_get):
        """A connection whose google_resource already exists must update, not duplicate."""
        resource = 'people/existing001'
        partner = self.env['res.partner'].create({
            'name': 'Old Name',
            'google_resource': resource,
        })
        mock_get.return_value = _mock_response(
            json_data={'connections': [
                self._google_connection(first='New', last='Name',
                                        resource=resource)]})
        self.company.action_import_google_contacts()
        partner.invalidate_recordset()
        self.assertEqual(partner.name, 'New Name')

    @patch('odoo.addons.odoo_google_contact_integration.models.res_company.requests.get')
    def test_import_empty_connections_no_partner_created(self, mock_get):
        """Empty connections list must not create any partners."""
        mock_get.return_value = _mock_response(json_data={'connections': []})
        before = self.env['res.partner'].search_count([])
        self.company.action_import_google_contacts()
        self.assertEqual(self.env['res.partner'].search_count([]), before)

    @patch('odoo.addons.odoo_google_contact_integration.models.res_company.requests.get')
    def test_import_raises_on_api_error(self, mock_get):
        """A non-200 response must raise ValidationError."""
        mock_get.return_value = _mock_response(
            status_code=401, text='Unauthorized')
        with self.assertRaises(ValidationError):
            self.company.action_import_google_contacts()


    @patch('odoo.addons.odoo_google_contact_integration.models.res_company.requests.get')
    def test_import_maps_first_name(self, mock_get):
        """Imported partner must have first_name  set correctly."""
        mock_get.return_value = _mock_response(
            json_data={'connections': [

                self._google_connection(first='Alice', last='Smith',
                                        resource='people/c_fn_test')]})
        self.company.action_import_google_contacts()
        partner = self.env['res.partner'].search(
            [('google_resource', '=', 'people/c_fn_test')], limit=1)
        self.assertEqual(partner.first_name, 'Alice')

    @patch('odoo.addons.odoo_google_contact_integration.models.res_company.requests.get')
    def test_import_maps_phone(self, mock_get):
        """Imported partner must have  phone populated."""
        mock_get.return_value = _mock_response(
            json_data={'connections': [
                self._google_connection(email='test@mail.com',
                                        phone='+1234567890',
                                        resource='people/c_ep')]})
        self.company.action_import_google_contacts()
        partner = self.env['res.partner'].search(
            [('google_resource', '=', 'people/c_ep')], limit=1)

        self.assertEqual(partner.phone, '+1234567890')



    @patch('odoo.addons.odoo_google_contact_integration.models.res_company.requests.get')
    def test_import_uses_bearer_token_in_header(self, mock_get):
        """API call must include Bearer token from company access token."""
        mock_get.return_value = _mock_response(json_data={'connections': []})
        self.company.action_import_google_contacts()
        headers_sent = mock_get.call_args[1].get('headers') or {}
        self.assertIn('valid-access-token',
                      headers_sent.get('Authorization', ''))
