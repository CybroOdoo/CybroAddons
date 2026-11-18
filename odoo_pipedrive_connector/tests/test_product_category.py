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

    @patch('requests.put')
    def test_write_multiple_categories(self, mock_put):
        """Renaming several categories updates each one in Pipedrive."""
        mock_put.return_value.json.return_value = {}
        categories = self.env['product.category']
        for reference in ('2004', '2005'):
            category = self.env['product.category'].create({
                'name': f'Category {reference}',
                'pipedrive_reference': reference,
            })
            self.env['pipedrive.record'].create({
                'pipedrive_reference': reference,
                'record_type': 'categ',
                'odoo_ref': category.id,
            })
            categories |= category
        categories.write({'name': 'Same Name'})
        self.assertEqual(mock_put.call_count, 2)

    @patch('requests.delete')
    def test_unlink_category_error(self, mock_delete):
        """Test validation error while deleting category."""
        mock_delete.return_value.json.return_value = {
            'error': 'Category Error'
        }
        category = self.env['product.category'].create({
            'name': 'Error Delete Category',
            'pipedrive_reference': '2006',
        })
        self.env['pipedrive.record'].create({
            'pipedrive_reference': '2006',
            'record_type': 'categ',
            'odoo_ref': category.id,
        })
        with self.assertRaises(ValidationError):
            category.unlink()
