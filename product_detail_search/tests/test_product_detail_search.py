# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo.tests.common import TransactionCase


class TestProductDetailSearch(TransactionCase):
    """Test the barcode-based product lookup used by the POS Find Product
    dialog and the Inventory dashboard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax = cls.env['account.tax'].create({
            'name': 'Product Detail Search Test Tax',
            'amount': 15,
            'type_tax_use': 'sale',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Barcode Test Product (Red, XL)',
            'barcode': 'PDS000001',
            'default_code': 'PDS-001',
            'list_price': 100.0,
            'taxes_id': [(6, 0, cls.tax.ids)],
        })
        cls.product_no_tax = cls.env['product.product'].create({
            'name': 'Barcode Test Product No Tax (Blue, M)',
            'barcode': 'PDS000002',
            'default_code': 'PDS-002',
            'list_price': 50.0,
            'taxes_id': [(6, 0, [])],
        })

    def test_search_by_known_barcode_returns_product_details(self):
        result = self.env['product.template'].product_detail_search(
            self.product.barcode
        )
        self.assertNotEqual(result, False)
        details = result[0]
        self.assertEqual(details['id'], self.product.id)
        self.assertEqual(details['display_name'], self.product.display_name)
        self.assertEqual(details['barcode'], 'PDS000001')
        self.assertEqual(details['default_code'], 'PDS-001')
        self.assertEqual(details['list_price'], 100.0)
        self.assertEqual(details['category'], self.product.categ_id.name)

    def test_search_by_unknown_barcode_returns_false(self):
        result = self.env['product.template'].product_detail_search(
            'NON_EXISTENT_BARCODE'
        )
        self.assertFalse(result)

    def test_search_includes_tax_name_when_taxes_are_set(self):
        result = self.env['product.template'].product_detail_search(
            self.product.barcode
        )
        self.assertEqual(result[0]['tax_amount'], self.tax.name)

    def test_search_reports_no_tax_when_no_taxes_are_set(self):
        result = self.env['product.template'].product_detail_search(
            self.product_no_tax.barcode
        )
        self.assertEqual(result[0]['tax_amount'], 'No tax')

    def test_search_extracts_specification_from_display_name(self):
        result = self.env['product.template'].product_detail_search(
            self.product.barcode
        )
        self.assertEqual(result[0]['specification'], ['Red', 'XL'])

    def test_search_reports_currency_symbol(self):
        result = self.env['product.template'].product_detail_search(
            self.product.barcode
        )
        self.assertEqual(
            result[0]['symbol'], self.product.currency_id.symbol
        )

    def test_get_selection_label_returns_translated_label(self):
        selection = dict(
            self.env['product.product'].fields_get(
                allfields=['type'])['type']['selection']
        )
        label = self.env['product.template'].get_selection_label(
            'product.product', 'type', 'consu'
        )
        self.assertEqual(label, selection['consu'])
