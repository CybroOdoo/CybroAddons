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


def _mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    """Tests for product.template Pipedrive overrides."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.api_key = 'test-api-key'
        cls.company.product_synced = False
        cls.PipedriveRecord = cls.env['pipedrive.record']

    def test_01_pipedrive_reference_field(self):
        """pipedrive_reference field exists on product.template."""
        product = self.env['product.template'].create({
            'name': 'Ref Product', 'list_price': 10.0,
            'pipedrive_reference': 'PD-PROD-1',
        })
        self.assertEqual(product.pipedrive_reference, 'PD-PROD-1')

    def test_02_update_from_pipedrive_field(self):
        """update_from_pipedrive boolean field defaults to False."""
        product = self.env['product.template'].create({
            'name': 'Flag Product', 'list_price': 10.0,
        })
        self.assertFalse(product.update_from_pipedrive)

    @patch('odoo.addons.odoo_pipedrive_connector.models.product_template.requests.put')
    def test_03_write_synced_product_calls_api(self, mock_put):
        """Writing to a synced product sends PUT to Pipedrive."""
        product = self.env['product.template'].create({
            'name': 'Synced Product', 'list_price': 100.0,
        })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'pd-prod-10',
            'record_type': 'product',
            'odoo_ref': product.id,
        })
        mock_put.return_value = _mock_response({'success': True, 'data': {}})
        product.write({'name': 'Updated Synced Product'})
        mock_put.assert_called_once()

    @patch('odoo.addons.odoo_pipedrive_connector.models.product_template.requests.put')
    def test_04_write_unsynced_product_no_api(self, mock_put):
        """Writing to an un-synced product does NOT call the API."""
        product = self.env['product.template'].create({
            'name': 'Local Product', 'list_price': 50.0,
        })
        product.write({'name': 'Still Local'})
        mock_put.assert_not_called()

    @patch('odoo.addons.odoo_pipedrive_connector.models.product_template.requests.put')
    def test_05_write_list_price_sends_prices(self, mock_put):
        """Writing list_price includes prices in Pipedrive payload."""
        product = self.env['product.template'].create({
            'name': 'Price Product', 'list_price': 100.0,
        })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'pd-prod-price',
            'record_type': 'product',
            'odoo_ref': product.id,
        })
        mock_put.return_value = _mock_response({'success': True, 'data': {}})
        product.write({'list_price': 200.0})
        mock_put.assert_called_once()

    @patch('odoo.addons.odoo_pipedrive_connector.models.product_template.requests.delete')
    def test_06_unlink_synced_product(self, mock_delete):
        """Deleting a synced product sends DELETE to Pipedrive."""
        product = self.env['product.template'].create({
            'name': 'Delete Product', 'list_price': 30.0,
        })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'pd-prod-del',
            'record_type': 'product',
            'odoo_ref': product.id,
        })
        mock_delete.return_value = _mock_response({'success': True})
        product.unlink()
        mock_delete.assert_called_once()

    @patch('odoo.addons.odoo_pipedrive_connector.models.product_template.requests.delete')
    def test_07_unlink_unsynced_product(self, mock_delete):
        """Deleting an un-synced product does NOT call the API."""
        product = self.env['product.template'].create({
            'name': 'Local Delete Product', 'list_price': 20.0,
        })
        product.unlink()
        mock_delete.assert_not_called()

    @patch('odoo.addons.odoo_pipedrive_connector.models.product_template.requests.post')
    def test_08_create_product_with_sync(self, mock_post):
        """Creating a product with product_synced=True exports to Pipedrive."""
        self.company.product_synced = True
        mock_post.return_value = _mock_response({
            'success': True, 'data': {'id': 'new-prod-1'},
        })
        product = self.env['product.template'].create({
            'name': 'Auto Export Product',
            'list_price': 150.0,
            'standard_price': 80.0,
        })
        self.assertTrue(product.exists())
        mock_post.assert_called_once()

    def test_09_create_product_without_sync(self):
        """Creating a product with product_synced=False does no export."""
        self.company.product_synced = False
        product = self.env['product.template'].create({
            'name': 'No Export Product', 'list_price': 50.0,
        })
        self.assertTrue(product.exists())

    def test_10_calculate_total_tax_percentage_percent(self):
        """calculate_total_tax_percentage on product.template for percent tax."""
        product = self.env['product.template'].create({
            'name': 'Tax Calc Product', 'list_price': 100.0,
        })
        tax = self.env['account.tax'].create({
            'name': 'Test 10%', 'amount_type': 'percent',
            'type_tax_use': 'sale', 'amount': 10.0,
        })
        result = product.calculate_total_tax_percentage(tax)
        self.assertEqual(result, 10.0)

    def test_11_calculate_total_tax_percentage_fixed(self):
        """calculate_total_tax_percentage on product.template for fixed tax."""
        product = self.env['product.template'].create({
            'name': 'Fixed Tax Calc', 'list_price': 200.0,
        })
        tax = self.env['account.tax'].create({
            'name': 'Fixed 10', 'amount_type': 'fixed',
            'type_tax_use': 'sale', 'amount': 10.0,
        })
        result = product.calculate_total_tax_percentage(tax)
        # (10 / 200) * 100 = 5.0
        self.assertEqual(result, 5.0)
