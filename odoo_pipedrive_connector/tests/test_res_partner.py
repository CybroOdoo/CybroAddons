# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
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
################################################################################
from unittest.mock import patch
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductCategory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.api_key = 'test_api_key'

    @patch('requests.put')
    def test_write_product_category(self, mock_put):
        """Test updating category in Pipedrive."""
        mock_put.return_value.json.return_value = {}
        category = self.env['product.category'].create({
            'name': 'Test Category',
            'pipedrive_reference': '2001',
        })

        self.env['pipedrive.record'].create({
            'pipedrive_reference': '2001',
            'record_type': 'categ',
            'odoo_ref': category.id,
        })
        category.write({
            'name': 'Updated Category'
        })
        self.assertEqual(
            category.name,
            'Updated Category'
        )

    @patch('requests.delete')
    def test_unlink_product_category(self, mock_delete):
        """Test deleting category from Pipedrive."""
        mock_delete.return_value.json.return_value = {}
        category = self.env['product.category'].create({
            'name': 'Delete Category',
            'pipedrive_reference': '2002',
        })
        self.env['pipedrive.record'].create({
            'pipedrive_reference': '2002',
            'record_type': 'categ',
            'odoo_ref': category.id,
        })
        category.unlink()
        existing_category = self.env['product.category'].search([
            ('id', '=', category.id)
        ])
        self.assertFalse(existing_category)

    @patch('requests.put')
    def test_category_validation_error(self, mock_put):
        """Test validation error while updating category."""
        mock_put.return_value.json.return_value = {
            'error': 'Category Error'
        }
        category = self.env['product.category'].create({
            'name': 'Error Category',
            'pipedrive_reference': '2003',
        })
        self.env['pipedrive.record'].create({
            'pipedrive_reference': '2003',
            'record_type': 'categ',
            'odoo_ref': category.id,
        })
        with self.assertRaises(ValidationError):
            category.write({
                'name': 'Updated Error Category'
            })
