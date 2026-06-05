# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


def _mock_response(json_data, status_code=200):
    """Helper to build a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):
    """Tests for res.company Pipedrive integration methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.api_key = 'test-api-key-12345'
        cls.PipedriveRecord = cls.env['pipedrive.record']

    def test_01_sync_products_no_api_key(self):
        """action_sync_products raises ValidationError without API key."""
        self.company.api_key = False
        with self.assertRaises(ValidationError):
            self.company.action_sync_products()

    def test_02_sync_contacts_no_api_key(self):
        """action_sync_contacts raises ValidationError without API key."""
        self.company.api_key = False
        with self.assertRaises(ValidationError):
            self.company.action_sync_contacts()

    def test_03_sync_leads_no_api_key(self):
        """action_sync_leads raises ValidationError without API key."""
        self.company.api_key = False
        with self.assertRaises(ValidationError):
            self.company.action_sync_leads()

    def test_04_calculate_tax_percent(self):
        """calculate_total_tax_percentage handles percentage taxes."""
        product = self.env['product.template'].create({
            'name': 'Tax Test Product',
            'list_price': 100.0,
        })
        tax = self.env['account.tax'].create({
            'name': 'Test 15%',
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'amount': 15.0,
        })
        product.taxes_id = [(6, 0, [tax.id])]
        result = self.company.calculate_total_tax_percentage(product)
        self.assertEqual(result, 15.0)

    def test_05_calculate_tax_fixed(self):
        """calculate_total_tax_percentage handles fixed taxes."""
        product = self.env['product.template'].create({
            'name': 'Fixed Tax Product',
            'list_price': 200.0,
        })
        tax = self.env['account.tax'].create({
            'name': 'Fixed 20',
            'amount_type': 'fixed',
            'type_tax_use': 'sale',
            'amount': 20.0,
        })
        product.taxes_id = [(6, 0, [tax.id])]
        result = self.company.calculate_total_tax_percentage(product)
        self.assertEqual(result, 10.0)

    def test_06_calculate_tax_no_taxes(self):
        """calculate_total_tax_percentage returns 0 when no taxes."""
        product = self.env['product.template'].create({
            'name': 'No Tax Product',
            'list_price': 50.0,
            'taxes_id': [(5, 0, 0)],
        })
        result = self.company.calculate_total_tax_percentage(product)
        self.assertEqual(result, 0.0)

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.get')
    def test_07_get_products_creates_product(self, mock_get):
        """get_products creates a product.template and pipedrive.record."""
        # get_products first calls create_product_category (GET productFields),
        # then GET products — use side_effect for sequential responses
        category_response = _mock_response({
            'success': True,
            'data': [{'key': 'category', 'options': []}],
        })
        products_response = _mock_response({
            'success': True,
            'data': [{
                'id': 501, 'name': 'Imported Product', 'description': 'Desc',
                'unit': None, 'category': None,
                'prices': [{'price': 50.0, 'cost': 25.0, 'currency': 'USD'}],
                'tax': 0,
            }],
        })
        mock_get.side_effect = [products_response, category_response]
        self.company.get_products()
        rec = self.PipedriveRecord.search([
            ('pipedrive_reference', '=', '501'),
            ('record_type', '=', 'product'),
        ])
        self.assertTrue(rec.exists())
        product = self.env['product.template'].browse(rec.odoo_ref)
        self.assertEqual(product.name, 'Imported Product')

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.get')
    def test_08_get_products_api_failure(self, mock_get):
        """get_products raises ValidationError on API failure."""
        mock_get.return_value = _mock_response({
            'success': False, 'error': 'Unauthorized', 'error_info': 'Bad key',
        })
        with self.assertRaises(ValidationError):
            self.company.get_products()

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.get')
    def test_09_get_contacts_creates_partner(self, mock_get):
        """get_contacts creates a res.partner and pipedrive.record."""
        mock_get.return_value = _mock_response({
            'success': True,
            'data': [{
                'id': 601, 'name': 'Jane Doe',
                'email': [{'value': 'jane@example.com'}],
                'phone': [{'value': '+1234567890'}],
            }],
        })
        self.company.get_contacts()
        rec = self.PipedriveRecord.search([
            ('pipedrive_reference', '=', '601'),
            ('record_type', '=', 'partner'),
        ])
        self.assertTrue(rec.exists())

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.get')
    def test_10_get_leads_creates_lead(self, mock_get):
        """get_leads creates a crm.lead and pipedrive.record."""
        mock_get.return_value = _mock_response({
            'success': True,
            'data': [{'id': 'lead-uuid-1', 'title': 'Test Lead', 'value': None}],
        })
        self.company.get_leads()
        rec = self.PipedriveRecord.search([
            ('pipedrive_reference', '=', 'lead-uuid-1'),
            ('record_type', '=', 'lead'),
        ])
        self.assertTrue(rec.exists())
        lead = self.env['crm.lead'].browse(rec.odoo_ref)
        self.assertEqual(lead.name, 'Test Lead')

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.post')
    def test_11_export_products(self, mock_post):
        """export_products_to_pipedrive exports unlinked products."""
        product = self.env['product.template'].create({
            'name': 'Export Me', 'list_price': 75.0, 'taxes_id': [(5, 0, 0)],
        })
        mock_post.return_value = _mock_response({
            'success': True, 'data': {'id': 701},
        })
        self.company.export_products_to_pipedrive()
        rec = self.PipedriveRecord.search([
            ('record_type', '=', 'product'), ('odoo_ref', '=', product.id),
        ])
        self.assertTrue(rec.exists())
        self.assertEqual(rec.pipedrive_reference, '701')

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.post')
    def test_12_export_contacts(self, mock_post):
        """export_contacts_to_pipedrive exports unlinked partners."""
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({
                'name': 'Export Partner', 'email': 'export@test.com',
            })
        mock_post.return_value = _mock_response({
            'success': True, 'data': {'id': 801},
        })
        self.company.export_contacts_to_pipedrive()
        rec = self.PipedriveRecord.search([
            ('record_type', '=', 'partner'), ('odoo_ref', '=', partner.id),
        ])
        self.assertTrue(rec.exists())

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.post')
    def test_13_export_leads(self, mock_post):
        """export_leads_to_pipedrive exports leads with a partner."""
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({
                'name': 'Lead Partner', 'pipedrive_reference': '900',
            })
        self.PipedriveRecord.create({
            'pipedrive_reference': '900', 'record_type': 'partner',
            'odoo_ref': partner.id,
        })
        lead = self.env['crm.lead'].create({
            'name': 'Export Lead', 'partner_id': partner.id,
            'expected_revenue': 5000.0,
        })
        # The code calls int() on pipedrive_reference, so use a numeric id
        mock_post.return_value = _mock_response({
            'success': True, 'data': {'id': '7001'},
        })
        self.company.export_leads_to_pipedrive()
        rec = self.PipedriveRecord.search([
            ('record_type', '=', 'lead'), ('odoo_ref', '=', lead.id),
        ])
        self.assertTrue(rec.exists())

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.post')
    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.get')
    def test_14_create_webhook_new(self, mock_get, mock_post):
        """create_webhook creates a new webhook when none exists."""
        mock_get.return_value = _mock_response({'success': True, 'data': []})
        mock_post.return_value = _mock_response({
            'success': True, 'data': {'id': 1},
        })
        self.company.create_webhook('create', '/add_pipedrive_product', 'product')
        mock_post.assert_called_once()

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.post')
    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.get')
    def test_15_create_webhook_already_exists(self, mock_get, mock_post):
        """create_webhook does NOT create a duplicate webhook."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        mock_get.return_value = _mock_response({
            'success': True,
            'data': [{
                'event_action': 'create', 'event_object': 'product',
                'subscription_url': base_url + '/add_pipedrive_product',
            }],
        })
        self.company.create_webhook('create', '/add_pipedrive_product', 'product')
        mock_post.assert_not_called()

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.post')
    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.get')
    def test_16_action_sync_products_full(self, mock_get, mock_post):
        """action_sync_products sets product_synced and returns notification."""
        # GET returns category data (productFields) and empty products
        mock_get.return_value = _mock_response({
            'success': True, 'data': [],
        })
        # POST (export + webhooks) must return dict data with 'id' key
        mock_post.return_value = _mock_response({
            'success': True, 'data': {'id': 9999},
        })
        result = self.company.action_sync_products()
        self.assertTrue(self.company.product_synced)
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.get')
    def test_17_create_product_category(self, mock_get):
        """create_product_category creates categories from API data."""
        mock_get.return_value = _mock_response({
            'success': True,
            'data': [{'key': 'category', 'options': [
                {'id': 50, 'label': 'Pipedrive Category A'},
            ]}],
        })
        self.company.create_product_category()
        categ = self.env['product.category'].search([
            ('name', '=', 'Pipedrive Category A'),
        ])
        self.assertTrue(categ.exists())
