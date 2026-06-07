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
from unittest.mock import patch, Mock
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.company.api_key = 'test_api'
        cls.company.product_synced = True

    @patch('requests.post')
    def test_create_product(self, mock_post):
        mock_post.return_value.json.return_value = {
            'success': True,
            'data': {
                'id': 5001
            }
        }
        product = self.env['product.template'].create({
            'name': 'Test Product',
            'list_price': 100,
        })

        self.assertTrue(product)

    @patch('requests.post')
    def test_calculate_tax_percentage(self, mock_post):
        """Test tax percentage calculation."""

        tax = self.env['account.tax'].create({
            'name': 'GST',
            'amount': 10,
            'amount_type': 'percent',
            'type_tax_use': 'sale'
        })

        product = self.env['product.template'].create({
            'name': 'Tax Product',
            'list_price': 100,
            'taxes_id': [(4, tax.id)]
        })
        percentage = product.calculate_total_tax_percentage(tax)
        self.assertEqual(
            percentage,
            10
        )
        mock_post.return_value.json.return_value = {
            'success': True,
            'data': {
                'id': 5002
            }
        }
