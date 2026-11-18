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
import json
from unittest.mock import patch
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from .common import mock_response


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.company.api_key = 'test_api'
        cls.company.product_synced = True
        tax_model = cls.env['account.tax']
        cls.percent_tax = tax_model.create(
            {'name': 'GST', 'amount': 10, 'amount_type': 'percent',
             'type_tax_use': 'sale'})
        cls.child_tax = tax_model.create(
            {'name': 'Child 5', 'amount': 5, 'amount_type': 'percent',
             'type_tax_use': 'none'})
        cls.group_tax = tax_model.create(
            {'name': 'Group', 'amount_type': 'group',
             'children_tax_ids': [(6, 0, cls.child_tax.ids)]})
        cls.fixed_tax = tax_model.create(
            {'name': 'Fixed 20', 'amount': 20, 'amount_type': 'fixed'})
        cls.division_tax = tax_model.create(
            {'name': 'Included 8', 'amount': 8, 'amount_type': 'division'})

    def _create_synced_products(self, count=1):
        """Create products that already exist in Pipedrive"""
        self.company.product_synced = False
        products = self.env['product.template']
        for index in range(count):
            product = self.env['product.template'].create(
                {'name': f'Synced Product {index}', 'list_price': 100.0})
            self.env['pipedrive.record'].create({
                'pipedrive_reference': str(5100 + index),
                'record_type': 'product',
                'odoo_ref': product.id,
            })
            products |= product
        self.company.product_synced = True
        return products

    @patch('requests.post')
    def test_create_product(self, mock_post):
        mock_post.return_value = mock_response(
            {'success': True, 'data': {'id': 5001}})
        product = self.env['product.template'].create({
            'name': 'Test Product',
            'list_price': 100,
            'taxes_id': [(6, 0, (self.percent_tax | self.group_tax
                                 | self.fixed_tax).ids)],
        })
        self.assertEqual(product.pipedrive_reference, '5001')
        # 10 + 5 + (20 / 100 * 100)
        self.assertEqual(mock_post.call_args.kwargs['json']['tax'], 35.0)

    @patch('requests.post')
    def test_create_product_already_synced(self, mock_post):
        """Products coming from Pipedrive are not sent back."""
        self.env['product.template'].create(
            {'name': 'Imported Product', 'pipedrive_reference': '5002'})
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_create_product_error(self, mock_post):
        mock_post.return_value = mock_response(
            {'success': False, 'error': 'Product not created',
             'error_info': 'Invalid price'})
        with self.assertRaises(ValidationError):
            self.env['product.template'].create({'name': 'Failing Product'})

    def test_calculate_tax_percentage(self):
        """Tax percentage for every tax computation type."""
        product = self.env['product.template'].new(
            {'name': 'Tax Product', 'list_price': 200})
        self.assertEqual(
            product.calculate_total_tax_percentage(self.percent_tax), 10)
        self.assertEqual(
            product.calculate_total_tax_percentage(self.group_tax), 5)
        self.assertEqual(
            product.calculate_total_tax_percentage(self.fixed_tax), 10)
        self.assertEqual(
            product.calculate_total_tax_percentage(self.division_tax), 8)
        product.list_price = 0
        self.assertEqual(
            product.calculate_total_tax_percentage(self.fixed_tax), 0)

    @patch('requests.put')
    def test_write_product(self, mock_put):
        """Name, unit, taxes and price changes are sent to Pipedrive."""
        product = self._create_synced_products()
        mock_put.return_value = mock_response({'success': True})
        product.write({
            'name': 'Renamed Product',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'taxes_id': [[6, 0, self.percent_tax.ids]],
            'list_price': 150.0,
        })
        sent = json.loads(mock_put.call_args.kwargs['data'])
        self.assertEqual(sent['name'], 'Renamed Product')
        self.assertEqual(sent['tax'], 10)
        self.assertEqual(sent['prices'][0]['price'], 150.0)

    @patch('requests.put')
    def test_write_multiple_products(self, mock_put):
        """Writing on several products updates each one in Pipedrive."""
        products = self._create_synced_products(count=2)
        mock_put.return_value = mock_response({'success': True})
        products.write({'list_price': 75.0})
        self.assertEqual(mock_put.call_count, 2)

    @patch('requests.put')
    def test_write_product_error(self, mock_put):
        product = self._create_synced_products()
        mock_put.return_value = mock_response({'error': 'Product not found'})
        with self.assertRaises(ValidationError):
            product.write({'name': 'Renamed Product'})

    @patch('requests.delete')
    def test_unlink_product(self, mock_delete):
        product = self._create_synced_products()
        mock_delete.return_value = mock_response({'success': True})
        product.unlink()
        self.assertFalse(product.exists())
        mock_delete.assert_called_once()

    @patch('requests.delete')
    def test_unlink_product_error(self, mock_delete):
        product = self._create_synced_products()
        mock_delete.return_value = mock_response({'error': 'Product not found'})
        with self.assertRaises(ValidationError):
            product.unlink()
