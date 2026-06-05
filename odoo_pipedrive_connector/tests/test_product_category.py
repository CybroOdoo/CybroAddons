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
class TestProductCategory(TransactionCase):
    """Tests for product.category Pipedrive overrides."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.api_key = 'test-api-key'
        cls.PipedriveRecord = cls.env['pipedrive.record']

    def test_01_pipedrive_reference_field(self):
        """pipedrive_reference field exists on product.category."""
        categ = self.env['product.category'].create({
            'name': 'Ref Category', 'pipedrive_reference': 'PD-CAT-1',
        })
        self.assertEqual(categ.pipedrive_reference, 'PD-CAT-1')

    @patch('odoo.addons.odoo_pipedrive_connector.models.product_category.requests.put')
    def test_02_write_synced_category_calls_api(self, mock_put):
        """Writing name to a synced category sends PUT to Pipedrive."""
        categ = self.env['product.category'].create({
            'name': 'Synced Category',
            'pipedrive_reference': 'pd-cat-10',
        })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'pd-cat-10',
            'record_type': 'categ',
            'odoo_ref': categ.id,
        })
        mock_put.return_value = _mock_response({'success': True, 'data': {}})
        categ.write({'name': 'Updated Category'})
        mock_put.assert_called_once()

    @patch('odoo.addons.odoo_pipedrive_connector.models.product_category.requests.put')
    def test_03_write_unsynced_category_no_api(self, mock_put):
        """Writing name to an un-synced category does NOT call the API."""
        categ = self.env['product.category'].create({
            'name': 'Local Category',
        })
        categ.write({'name': 'Still Local'})
        mock_put.assert_not_called()

    @patch('odoo.addons.odoo_pipedrive_connector.models.product_category.requests.put')
    def test_04_write_non_name_field_no_api(self, mock_put):
        """Writing a field other than name does NOT trigger API call."""
        categ = self.env['product.category'].create({
            'name': 'Non Name Category',
        })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'pd-cat-nn',
            'record_type': 'categ',
            'odoo_ref': categ.id,
        })
        # parent_id is not 'name', so no API call expected
        parent = self.env['product.category'].create({'name': 'Parent'})
        categ.write({'parent_id': parent.id})
        mock_put.assert_not_called()

    @patch('odoo.addons.odoo_pipedrive_connector.models.product_category.requests.delete')
    def test_05_unlink_synced_category(self, mock_delete):
        """Deleting a synced category sends DELETE to Pipedrive."""
        categ = self.env['product.category'].create({
            'name': 'Delete Category',
            'pipedrive_reference': 'pd-cat-del',
        })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'pd-cat-del',
            'record_type': 'categ',
            'odoo_ref': categ.id,
        })
        mock_delete.return_value = _mock_response({'success': True})
        categ.unlink()
        mock_delete.assert_called_once()

    @patch('odoo.addons.odoo_pipedrive_connector.models.product_category.requests.delete')
    def test_06_unlink_unsynced_category(self, mock_delete):
        """Deleting an un-synced category does NOT call the API."""
        categ = self.env['product.category'].create({
            'name': 'Local Delete Category',
        })
        categ.unlink()
        mock_delete.assert_not_called()

    def test_07_create_category_basic(self):
        """Basic category creation without Pipedrive interaction."""
        categ = self.env['product.category'].create({
            'name': 'Basic Category',
        })
        self.assertTrue(categ.exists())
        self.assertEqual(categ.name, 'Basic Category')
