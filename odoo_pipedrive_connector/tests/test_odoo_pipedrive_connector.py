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
import base64
import json
from unittest.mock import patch, Mock
from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged('post_install', '-at_install')
class TestOdooPipedriveConnector(HttpCase):
    """
    HttpCase tests for Pipedrive webhook controllers.
    Setup data for tests that involve pre-existing records (update, delete)
    is placed in setUpClass so it is committed by the framework and visible
    to the HTTP controller's separate DB transaction.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.sudo().pipedrive_webhook_token = 'test-webhook-token'
        # Data for test_update_contact_webhook
        cls.update_partner = cls.env['res.partner'].create({
            'name': 'Old Partner',
            'pipedrive_reference': '3002',
        })
        cls.env['pipedrive.record'].create({
            'pipedrive_reference': '3002',
            'record_type': 'partner',
            'odoo_ref': cls.update_partner.id,
        })
        cls.delete_partner = cls.env['res.partner'].create({
            'name': 'Delete Partner',
            'pipedrive_reference': '3003',
        })
        cls.env['pipedrive.record'].create({
            'pipedrive_reference': '3003',
            'record_type': 'partner',
            'odoo_ref': cls.delete_partner.id,
        })
        # Data for the product webhooks
        cls.env.company.product_synced = False
        cls.update_categ = cls.env['product.category'].create(
            {'name': 'Webhook Category'})
        cls.env['pipedrive.record'].create({
            'pipedrive_reference': '4101',
            'record_type': 'categ',
            'odoo_ref': cls.update_categ.id,
        })
        cls.update_product = cls.env['product.template'].create({
            'name': 'Old Product',
            'pipedrive_reference': '4001',
        })
        cls.env['pipedrive.record'].create({
            'pipedrive_reference': '4001',
            'record_type': 'product',
            'odoo_ref': cls.update_product.id,
        })
        cls.delete_product = cls.env['product.template'].create({
            'name': 'Delete Product',
            'pipedrive_reference': '4003',
        })
        cls.env['pipedrive.record'].create({
            'pipedrive_reference': '4003',
            'record_type': 'product',
            'odoo_ref': cls.delete_product.id,
        })

    def _post_webhook(self, route, payload, token='test-webhook-token'):
        headers = {'Content-Type': 'application/json'}
        if token:
            credentials = base64.b64encode(
                f'odoo:{token}'.encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'
        return self.url_open(route, data=json.dumps(payload), headers=headers)

    def test_webhook_requires_authentication(self):
        """Calls without the webhook secret are rejected."""
        payload = {
            'data': {
                'id': '3901',
                'name': 'Intruder',
                'phones': [],
                'emails': [],
            }
        }
        self._post_webhook('/add_pipedrive_contact', payload, token=None)
        self._post_webhook('/add_pipedrive_contact', payload, token='wrong')
        self.assertFalse(self.env['res.partner'].search(
            [('pipedrive_reference', '=', '3901')]))

    def test_update_product_webhook(self):
        """Test update product webhook updates the product details."""
        payload = {
            'data': {
                'id': '4001',
                'name': 'Updated Product',
                'description': 'Updated from Pipedrive',
                'unit': 'Units',
                'category': '4101',
                'prices': [{'currency': 'USD', 'price': 30.0, 'cost': 10.0}],
            }
        }
        with patch('requests.put', return_value=Mock(
                json=Mock(return_value={'success': True}))) as mock_put:
            self._post_webhook('/update_pipedrive_product', payload)
        # Changes received from Pipedrive are not pushed back to it
        mock_put.assert_not_called()
        self.update_product.invalidate_recordset()
        self.assertEqual(self.update_product.name, 'Updated Product')
        self.assertEqual(self.update_product.categ_id, self.update_categ)

    def test_update_product_webhook_without_match(self):
        """Empty payloads and unknown products are ignored."""
        self._post_webhook('/update_pipedrive_product', {'data': {}})
        self._post_webhook('/update_pipedrive_product',
                           {'data': {'id': '4999', 'name': 'Unknown'}})
        self.assertFalse(self.env['product.template'].search(
            [('name', '=', 'Unknown')]))

    def test_add_product_webhook(self):
        """Test add product webhook creates a product with its tax."""
        payload = {
            'meta': {'change_source': 'api'},
            'data': {
                'id': '4002',
                'name': 'Webhook Product',
                'description': 'Created in Pipedrive',
                'unit': 'Units',
                'category': '4101',
                'tax': 7.5,
                'prices': [{'currency': 'USD', 'price': 40.0, 'cost': 15.0}],
            }
        }
        with patch('requests.get', return_value=Mock(json=Mock(
                return_value={'success': True, 'data': []}))):
            self._post_webhook('/add_pipedrive_product', payload)
        product = self.env['product.template'].search(
            [('pipedrive_reference', '=', '4002')], limit=1)
        self.assertEqual(product.name, 'Webhook Product')
        self.assertEqual(product.categ_id, self.update_categ)
        self.assertEqual(product.taxes_id.amount, 7.5)

    def test_delete_product_webhook(self):
        """Test delete product webhook archives the product."""
        payload = {'meta': {'entity_id': '4003'}}
        self._post_webhook('/delete_pipedrive_product', payload)
        self.delete_product.invalidate_recordset()
        self.assertFalse(self.delete_product.active)

    def test_delete_contact_webhook_without_id(self):
        """Test delete contact webhook without an entity id."""
        response = self._post_webhook('/delete_pipedrive_contact',
                                      {'meta': {}})
        self.assertIn('No entity_id found', response.text)

    def test_add_contact_webhook(self):
        """Test add contact webhook creates a new partner."""
        payload = {
            'data': {
                'id': '3001',
                'name': 'Webhook Partner',
                'phones': [{'value': '9876543210'}],
                'emails': [{'value': 'webhook@test.com'}],
            }
        }
        self._post_webhook('/add_pipedrive_contact', payload)
        partner = self.env['res.partner'].search([
            ('pipedrive_reference', '=', '3001')
        ], limit=1)
        self.assertTrue(partner)

    def test_update_contact_webhook(self):
        """Test update contact webhook updates an existing partner's name."""
        payload = {
            'data': {
                'id': '3002',
                'name': 'Updated Partner',
                'phones': [{'value': '9999999999'}],
                'emails': [{'value': 'updated@test.com'}],
            }
        }
        mock_response = Mock()
        mock_response.json.return_value = {'success': True}

        with patch('requests.put', return_value=mock_response):
            self._post_webhook('/update_pipedrive_contact', payload)
        self.update_partner.invalidate_recordset()
        self.assertEqual(self.update_partner.name, 'Updated Partner')

    def test_delete_contact_webhook(self):
        """
        Test delete contact webhook archives an existing partner.
        """
        payload = {
            'meta': {
                'entity_id': '3003'
            },
            'data': {
                'id': '3003'
            }
        }

        self._post_webhook('/delete_pipedrive_contact', payload)
        self.delete_partner.invalidate_recordset()
        deleted_partner = self.env['res.partner'].with_context(
            active_test=False
        ).search([
            ('pipedrive_reference', '=', '3003')
        ], limit=1)
        self.assertTrue(deleted_partner)
        self.assertFalse(deleted_partner.active)
