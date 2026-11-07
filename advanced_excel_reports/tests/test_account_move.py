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
    """Minimal response object used by account.move XLSX report tests."""

    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestAccountMoveExcelReport(TransactionCase):
    """Test account.move XLSX report action and generated workbook content."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Account Move XLSX Partner',
            'street': 'Invoice Street',
            'zip': '12345',
            'phone': '555-0199',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Account Move XLSX Product',
            'list_price': 200.0,
            'standard_price': 50.0,
        })
        cls.income_account = cls._get_account('income')
        cls.expense_account = cls._get_account('expense')
        cls.invoice = cls._create_move(
            move_type='out_invoice',
            name='INV-XLSX-CASE',
            payment_reference='INV-XLSX-REF',
            line_name='Invoice XLSX Line',
            account=cls.income_account,
        )
        cls.vendor_bill = cls._create_move(
            move_type='in_invoice',
            name='BILL-XLSX-CASE',
            payment_reference='BILL-XLSX-REF',
            line_name='Vendor Bill XLSX Line',
            account=cls.expense_account,
        )
    @classmethod
    def _get_account(cls, account_kind):
        account = cls.env['account.account'].search([
            ('account_type', '=', account_kind),
            ('company_ids', 'in', cls.env.company.id),
        ], limit=1)
        if not account:

            account = cls.env['account.account'].search([
                ('account_type', '=', account_kind),
            ], limit=1)
        if not account:
            raise AssertionError("A %s account is required." % account_kind)
        return account

    @classmethod
    def _create_move(cls, move_type, name, payment_reference, line_name,
                     account):
        move = cls.env['account.move'].create({
            'partner_id': cls.partner.id,
            'move_type': move_type,
            'name': name,
            'payment_reference': payment_reference,
            'invoice_line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'name': line_name,
                'quantity': 2.0,
                'discount': 10.0,
                'price_unit': 100.0,
                'account_id': account.id,
            })],
        })
        return move

    def _get_xlsx_shared_strings(self, move):

        response = XLSXResponse()
        move.get_xlsx_report(move.ids, response)
        response.stream.seek(0)
        self.assertGreater(len(response.stream.getvalue()), 0)

        with zipfile.ZipFile(response.stream) as workbook:

            self.assertIn('xl/workbook.xml', workbook.namelist())
            shared_strings = workbook.read('xl/sharedStrings.xml').decode()
            return shared_strings

    def test_print_excel_report_action(self):
        """print_excel_report returns the expected XLSX action payload."""
        action = self.invoice.with_context(
            active_ids=self.invoice.ids
        ).print_excel_report()

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(action['data']['model'], 'account.move')
        self.assertEqual(action['data']['output_format'], 'xlsx')
        self.assertEqual(action['data']['report_name'], 'Invoice Excel Report')
        self.assertEqual(
            json.loads(action['data']['options']),
            self.invoice.ids
        )

    def test_get_xlsx_report_invoice_content(self):
        """get_xlsx_report writes invoice header and line values."""
        shared_strings = self._get_xlsx_shared_strings(self.invoice)

        expected_values = [
            'INVOICE - %s' % self.invoice.name,
            'Company Name : %s' % self.env.company.name,
            'Customer/Vendor Name',
            self.partner.name,
            'Date',
            'Journal',
            'Currency',
            'State',
            'Source Document',
            'INV-XLSX-REF',
            'Product',
            'Description',
            'Quantity',
            'Account',
            'Discount %',
            'Unit Price',
            'Tax',
            'Subtotal',
            self.product.name,
            'Invoice XLSX Line',
            self.income_account.display_name,
            'Total Amount',
        ]
        for value in expected_values:
            self.assertIn(value, shared_strings)

    def test_get_xlsx_report_vendor_bill_content(self):
        """get_xlsx_report writes vendor bill header and line values."""
        shared_strings = self._get_xlsx_shared_strings(self.vendor_bill)

        expected_values = [
            'VENDOR BILL - %s' % self.vendor_bill.name,
            'Company Name : %s' % self.env.company.name,
            'Customer/Vendor Name',
            self.partner.name,
            'Source Document',
            'BILL-XLSX-REF',
            self.product.name,
            'Vendor Bill XLSX Line',
            self.expense_account.display_name,
            'Total Amount',
        ]
        for value in expected_values:
            self.assertIn(value, shared_strings)

