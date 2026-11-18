# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
from unittest.mock import patch
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from .common import mock_response, route_responses

ERROR_RESPONSE = {'success': False, 'error': 'Bad request',
                  'error_info': 'Check the token'}


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'api_key': 'test_api_key',
            'product_synced': False,
            'contact_synced': False,
            'lead_synced': False,
        })
        cls.env['ir.config_parameter'].sudo().set_str(
            'web.base.url', 'https://pipedrive.example.com')

    def _sync_get_routes(self):
        """Pipedrive answers with no remote data and no webhooks"""
        return route_responses({
            'products': {'success': True, 'data': []},
            'persons': {'success': True, 'data': []},
            'leads': {'success': True, 'data': []},
            'webhooks': {'success': True, 'data': []},
        })

    def _sync_post_routes(self):
        return route_responses({
            'products': {'success': True, 'data': {'id': 1}},
            'persons': {'success': True, 'data': {'id': 2}},
            'leads': {'success': True, 'data': {'id': 'lead-1'}},
            'webhooks': {'success': True},
        })

    def test_sync_without_api_key(self):
        """All sync buttons need a Pipedrive token."""
        self.company.api_key = False
        with self.assertRaises(ValidationError):
            self.company.action_sync_products()
        with self.assertRaises(ValidationError):
            self.company.action_sync_contacts()
        with self.assertRaises(ValidationError):
            self.company.action_sync_leads()

    @patch('requests.post')
    @patch('requests.get')
    def test_action_sync_products(self, mock_get, mock_post):
        """Syncing products imports, exports and registers 3 webhooks."""
        mock_get.side_effect = self._sync_get_routes()
        mock_post.side_effect = self._sync_post_routes()
        self.company.action_sync_products()
        self.assertTrue(self.company.product_synced)
        webhook_posts = [c for c in mock_post.call_args_list
                         if c.args and c.args[0].endswith('/webhooks')]
        self.assertEqual(len(webhook_posts), 3)
        # A second click does nothing once products are synced
        mock_post.reset_mock()
        self.company.action_sync_products()
        mock_post.assert_not_called()

    @patch('requests.post')
    @patch('requests.get')
    def test_action_sync_contacts(self, mock_get, mock_post):
        mock_get.side_effect = self._sync_get_routes()
        mock_post.side_effect = self._sync_post_routes()
        self.company.action_sync_contacts()
        self.assertTrue(self.company.contact_synced)

    @patch('requests.post')
    @patch('requests.get')
    def test_action_sync_leads(self, mock_get, mock_post):
        mock_get.side_effect = self._sync_get_routes()
        mock_post.side_effect = self._sync_post_routes()
        self.company.action_sync_leads()
        self.assertTrue(self.company.lead_synced)

    @patch('requests.get')
    def test_get_products(self, mock_get):
        """Products and categories are imported from Pipedrive."""
        existing_categ = self.env['product.category'].create(
            {'name': 'Existing Pipedrive Category'})
        mock_get.side_effect = route_responses({
            'productFields': {'success': True, 'data': [
                {'key': 'name', 'options': []},
                {'key': 'category', 'options': [
                    {'id': 101, 'label': 'New Pipedrive Category'},
                    {'id': 102, 'label': 'Existing Pipedrive Category'},
                ]},
            ]},
            'products': {'success': True, 'data': [{
                'id': 9001,
                'name': 'Pipedrive Product',
                'description': 'Imported product',
                'unit': 'Units',
                'prices': [{'price': 50.0, 'cost': 20.0, 'currency': 'EUR'}],
                'tax': 12.5,
                'category': 101,
            }, {
                'id': 9002,
                'name': 'Pipedrive Product No Tax',
                'description': False,
                'unit': False,
                'prices': [{'price': 0, 'cost': 0, 'currency': 'USD'}],
                'tax': 0,
                'category': False,
            }]},
        })
        self.company.get_products()
        product = self.env['product.template'].search(
            [('pipedrive_reference', '=', '9001')])
        self.assertEqual(product.name, 'Pipedrive Product')
        self.assertEqual(product.list_price, 50.0)
        self.assertEqual(product.categ_id.name, 'New Pipedrive Category')
        self.assertEqual(product.taxes_id.amount, 12.5)
        self.assertTrue(self.env['product.template'].search(
            [('pipedrive_reference', '=', '9002')]))
        self.assertTrue(self.env['pipedrive.record'].search(
            [('record_type', '=', 'categ'),
             ('odoo_ref', '=', existing_categ.id)]))
        # Importing again does not duplicate the products
        self.company.get_products()
        self.assertEqual(self.env['product.template'].search_count(
            [('pipedrive_reference', '=', '9001')]), 1)

    @patch('requests.get')
    def test_get_products_error(self, mock_get):
        mock_get.return_value = mock_response(ERROR_RESPONSE)
        with self.assertRaises(ValidationError):
            self.company.get_products()

    @patch('requests.get')
    def test_create_product_category_error(self, mock_get):
        mock_get.return_value = mock_response(ERROR_RESPONSE)
        with self.assertRaises(ValidationError):
            self.company.create_product_category()

    @patch('requests.get')
    def test_get_contacts(self, mock_get):
        mock_get.return_value = mock_response({'success': True, 'data': [{
            'id': 7001,
            'name': 'Pipedrive Person',
            'phone': [{'value': '9876543210'}],
            'email': [{'value': 'person@example.com'}],
        }]})
        self.company.get_contacts()
        partner = self.env['res.partner'].search(
            [('pipedrive_reference', '=', '7001')])
        self.assertEqual(partner.email, 'person@example.com')
        self.assertTrue(self.env['pipedrive.record'].search(
            [('record_type', '=', 'partner'), ('odoo_ref', '=', partner.id)]))

    @patch('requests.get')
    def test_get_contacts_error(self, mock_get):
        mock_get.return_value = mock_response(ERROR_RESPONSE)
        with self.assertRaises(ValidationError):
            self.company.get_contacts()

    @patch('requests.get')
    def test_get_leads(self, mock_get):
        mock_get.return_value = mock_response({'success': True, 'data': [{
            'id': 'lead-uuid-1',
            'title': 'Pipedrive Lead',
            'value': {'amount': 100.0, 'currency': 'EUR'},
        }, {
            'id': 'lead-uuid-2',
            'title': 'Pipedrive Lead Without Value',
            'value': None,
        }]})
        self.company.get_leads()
        lead = self.env['crm.lead'].search(
            [('pipedrive_reference', '=', 'lead-uuid-1')])
        self.assertEqual(lead.name, 'Pipedrive Lead')
        self.assertTrue(lead.expected_revenue)
        lead_without_value = self.env['crm.lead'].search(
            [('pipedrive_reference', '=', 'lead-uuid-2')])
        self.assertEqual(lead_without_value.expected_revenue, 0)

    @patch('requests.get')
    def test_get_leads_error(self, mock_get):
        mock_get.return_value = mock_response(ERROR_RESPONSE)
        with self.assertRaises(ValidationError):
            self.company.get_leads()

    @patch('requests.post')
    def test_export_products_to_pipedrive(self, mock_post):
        product = self.env['product.template'].create(
            {'name': 'Export Product', 'list_price': 80.0})
        mock_post.return_value = mock_response(
            {'success': True, 'data': {'id': 6001}})
        self.company.export_products_to_pipedrive()
        self.assertEqual(product.pipedrive_reference, '6001')
        self.assertTrue(self.env['pipedrive.record'].search(
            [('record_type', '=', 'product'), ('odoo_ref', '=', product.id)]))

    @patch('requests.post')
    def test_export_products_error(self, mock_post):
        self.env['product.template'].create({'name': 'Export Error Product'})
        mock_post.return_value = mock_response(ERROR_RESPONSE)
        with self.assertRaises(ValidationError):
            self.company.export_products_to_pipedrive()

    @patch('requests.post')
    def test_export_contacts_to_pipedrive(self, mock_post):
        partner = self.env['res.partner'].create({'name': 'Export Partner'})
        mock_post.return_value = mock_response(
            {'success': True, 'data': {'id': 7101}})
        self.company.export_contacts_to_pipedrive()
        self.assertEqual(partner.pipedrive_reference, '7101')

    @patch('requests.post')
    def test_create_contact_error(self, mock_post):
        partner = self.env['res.partner'].create({'name': 'Error Partner'})
        mock_post.return_value = mock_response(
            {'success': False, 'error': 'Person not created'})
        with self.assertRaises(ValidationError):
            self.company.create_contact(partner)

    @patch('requests.post')
    def test_export_leads_to_pipedrive(self, mock_post):
        """Leads are exported and their customer is created in Pipedrive."""
        partner = self.env['res.partner'].create({'name': 'Lead Customer'})
        lead = self.env['crm.lead'].create(
            {'name': 'Export Lead', 'partner_id': partner.id,
             'expected_revenue': 500.0})
        mock_post.side_effect = route_responses({
            'persons': {'success': True, 'data': {'id': 7201}},
            'leads': {'success': True, 'data': {'id': 'lead-uuid-3'}},
        })
        self.company.export_leads_to_pipedrive()
        self.assertEqual(partner.pipedrive_reference, '7201')
        self.assertEqual(lead.pipedrive_reference, 'lead-uuid-3')

    @patch('requests.post')
    def test_export_leads_error(self, mock_post):
        partner = self.env['res.partner'].create({'name': 'Lead Customer'})
        self.env['crm.lead'].create(
            {'name': 'Export Lead Error', 'partner_id': partner.id})
        mock_post.side_effect = route_responses({
            'persons': {'success': True, 'data': {'id': 7301}},
            'leads': ERROR_RESPONSE,
        })
        with self.assertRaises(ValidationError):
            self.company.export_leads_to_pipedrive()

    @patch('requests.post')
    @patch('requests.get')
    def test_create_webhook(self, mock_get, mock_post):
        mock_get.return_value = mock_response({'success': True, 'data': []})
        mock_post.return_value = mock_response({'success': True})
        self.company.create_webhook(
            'create', '/add_pipedrive_product', 'product')
        payload = mock_post.call_args.kwargs['json']
        self.assertEqual(
            payload['subscription_url'],
            'https://pipedrive.example.com/add_pipedrive_product')
        self.assertEqual(payload['http_auth_user'], 'odoo')
        self.assertTrue(payload['http_auth_password'])
        self.assertEqual(payload['http_auth_password'],
                         self.company.sudo().pipedrive_webhook_token)

    @patch('requests.post')
    @patch('requests.get')
    def test_create_webhook_already_exists(self, mock_get, mock_post):
        mock_get.return_value = mock_response({'success': True, 'data': [{
            'id': 1,
            'event_action': 'create',
            'event_object': 'product',
            'subscription_url':
                'https://pipedrive.example.com/add_pipedrive_product',
            'http_auth_user': 'odoo',
        }]})
        self.company.create_webhook(
            'create', '/add_pipedrive_product', 'product')
        mock_post.assert_not_called()

    @patch('requests.delete')
    @patch('requests.post')
    @patch('requests.get')
    def test_create_webhook_replaces_unauthenticated(self, mock_get,
                                                     mock_post, mock_delete):
        """A webhook registered without credentials is recreated."""
        mock_get.return_value = mock_response({'success': True, 'data': [{
            'id': 7,
            'event_action': 'create',
            'event_object': 'product',
            'subscription_url':
                'https://pipedrive.example.com/add_pipedrive_product',
        }]})
        mock_post.return_value = mock_response({'success': True})
        self.company.create_webhook(
            'create', '/add_pipedrive_product', 'product')
        self.assertTrue(mock_delete.call_args.args[0].endswith('/webhooks/7'))
        self.assertEqual(mock_post.call_args.kwargs['json']['http_auth_user'],
                         'odoo')

    @patch('requests.post')
    @patch('requests.get')
    def test_create_webhook_error(self, mock_get, mock_post):
        mock_get.return_value = mock_response({'success': True, 'data': []})
        mock_post.return_value = mock_response({'success': False})
        with self.assertRaises(ValidationError):
            self.company.create_webhook(
                'create', '/add_pipedrive_product', 'product')

    def test_create_webhook_requires_https(self):
        self.env['ir.config_parameter'].sudo().set_str(
            'web.base.url', 'http://pipedrive.example.com')
        with self.assertRaises(ValidationError):
            self.company.create_webhook(
                'create', '/add_pipedrive_product', 'product')

    def test_calculate_total_tax_percentage(self):
        """Percent, group, fixed and price-included taxes are summed."""
        tax_model = self.env['account.tax']
        percent_tax = tax_model.create(
            {'name': 'Percent 10', 'amount': 10, 'amount_type': 'percent'})
        child_tax = tax_model.create(
            {'name': 'Child 5', 'amount': 5, 'amount_type': 'percent',
             'type_tax_use': 'none'})
        group_tax = tax_model.create(
            {'name': 'Group', 'amount_type': 'group',
             'children_tax_ids': [(6, 0, child_tax.ids)]})
        fixed_tax = tax_model.create(
            {'name': 'Fixed 20', 'amount': 20, 'amount_type': 'fixed'})
        division_tax = tax_model.create(
            {'name': 'Included 8', 'amount': 8, 'amount_type': 'division'})
        product = self.env['product.template'].create({
            'name': 'Taxed Product',
            'list_price': 200.0,
            'taxes_id': [(6, 0, (percent_tax | group_tax | fixed_tax
                                 | division_tax).ids)],
        })
        # 10 + 5 + (20 / 200 * 100) + 8
        self.assertAlmostEqual(
            self.company.calculate_total_tax_percentage(product), 33.0)
