# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import io
import json
import zipfile

from odoo.tests import tagged
from odoo.tests.common import TransactionCase





class XLSXResponse:
    """Minimal response object used by sale.order XLSX report tests."""

    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestSaleOrderExcelReport(TransactionCase):
    """Test sale.order XLSX report action and generated workbook content."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Sale Order XLSX Partner',
            'street': 'Sale Street',
            'zip': '67890',
            'phone': '555-0177',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Sale Order XLSX Product',
            'list_price': 125.0,
            'standard_price': 40.0,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'name': 'SO-XLSX-CASE',
            'client_order_ref': 'SO-XLSX-REF',
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'name': 'Sale Order XLSX Line',
                'product_uom_qty': 3.0,
                'price_unit': 125.0,
            })],
        })



    def _get_xlsx_shared_strings(self, sale_order):

        response = XLSXResponse()
        sale_order.get_xlsx_report(sale_order.ids, response)
        response.stream.seek(0)
        self.assertGreater(len(response.stream.getvalue()), 0)

        with zipfile.ZipFile(response.stream) as workbook:
            self.assertIn('xl/workbook.xml', workbook.namelist())
            shared_strings = workbook.read('xl/sharedStrings.xml').decode()
            return shared_strings

    def test_print_excel_report_action(self):
        """print_excel_report returns the expected XLSX action payload."""
        action = self.sale_order.with_context(
            active_ids=self.sale_order.ids
        ).print_excel_report()

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(action['data']['model'], 'sale.order')
        self.assertEqual(action['data']['output_format'], 'xlsx')
        self.assertEqual(
            action['data']['report_name'],
            'Sale/Quotation Excel Report'
        )
        self.assertEqual(
            json.loads(action['data']['options']),
            self.sale_order.ids
        )

    def test_get_xlsx_report_content(self):
        """get_xlsx_report writes sale order header and line values."""
        shared_strings = self._get_xlsx_shared_strings(self.sale_order)

        expected_values = [
            'SALE ORDER - %s' % self.sale_order.name,
            'Company Name : %s' % self.env.company.name,
            'Customer Name',
            self.partner.name,
            self.partner.street,
            self.partner.zip,
            self.partner.phone,
            'Date',
            'Payment Term',
            'Price List',
            'State',
            'Sales Team',
            'Sales Persons',
            'Source Document',
            'SO-XLSX-REF',
            'Fiscal Position',
            'Product',
            'Description',
            'Quantity',
            'Delivered',
            'Invoiced',
            'Unit Price',
            'Tax',
            'Subtotal',
            self.product.name,
            'Sale Order XLSX Line',
            'Total Amount',
        ]

        for value in expected_values:
            self.assertIn(value, shared_strings)

