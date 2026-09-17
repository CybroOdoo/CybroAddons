# -*- coding: utf-8 -*-
import io

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestVendorStatement(AccountKitCommon):

    def _post_bill(self, amount=400.0):
        self.init_invoice('in_invoice', partner=self.partner_b,
                          invoice_date='2020-02-01', amounts=[amount],
                          taxes=[], post=True)

    def test_vendor_statement_ids_lists_open_bills(self):
        """Open vendor bills populate vendor_statement_ids."""
        self._post_bill()
        self.assertTrue(self.partner_b.vendor_statement_ids)

    def test_statement_data_has_rows_and_totals(self):
        """The shared payload contains the bill rows and totals."""
        self._post_bill()
        data = self.partner_b._statement_data('in_invoice')
        self.assertTrue(data['my_data'], "The open bill is listed")
        self.assertTrue(data['total'])

    def test_vendor_print_xlsx_returns_xlsx_action(self):
        """Print Excel returns the xlsx client action for res.partner."""
        self._post_bill()
        action = self.partner_b.action_vendor_print_xlsx()
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(action['data']['model'], 'res.partner')

    def test_vendor_statement_workbook_builds(self):
        """The reused get_xlsx_report writes a valid workbook from vendor
        data (the path action_vendor_share_xlsx relies on)."""
        self._post_bill()
        data = self.partner_b._statement_data('in_invoice')
        buf = io.BytesIO()
        response = type('R', (object,), {'stream': buf})()
        self.partner_b.get_xlsx_report(data, response)
        self.assertTrue(buf.getvalue().startswith(b'PK'),
                        "A valid xlsx workbook is produced")

    def test_vendor_print_raises_without_bills(self):
        """A vendor with no open bills reports there is nothing to print."""
        vendor = self.env['res.partner'].create({'name': 'No Bills Vendor'})
        with self.assertRaises(ValidationError):
            vendor.action_vendor_print_pdf()
