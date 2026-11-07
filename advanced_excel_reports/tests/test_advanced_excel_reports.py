# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################

import io
import json
import zipfile
from unittest.mock import MagicMock, patch

from odoo.http import Response
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.addons.advanced_excel_reports.controllers.advanced_excel_reports import XLSXReportController




class XLSXResponse:
    """Minimal response object expected by get_xlsx_report."""

    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestAdvancedExcelReports(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Excel Report Partner',
            'street': 'Report Street',
            'phone': '555-0100',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Excel Report Product',
            'list_price': 100.0,
            'standard_price': 25.0,
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'name': 'Excel Sale Line',
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
            })],
        })


        income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.env.company.id),
        ], limit=1)
        if not income_account:
            income_account = cls.env['account.account'].search([
                ('account_type', '=', 'income'),
            ], limit=1)


        cls.invoice = cls.env['account.move'].create({
            'partner_id': cls.partner.id,
            'move_type': 'out_invoice',
            'name': 'INV-XLSX-TEST',
            'invoice_line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'name': 'Excel Invoice Line',
                'quantity': 1.0,
                'price_unit': 150.0,
                'account_id': income_account.id,
            })],
        })


        picking_type = cls.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', 'in', [False, cls.env.company.id]),
        ], limit=1)

        source_location = picking_type.default_location_src_id
        destination_location = (
            picking_type.default_location_dest_id
            or cls.env.ref('stock.stock_location_customers')
        )
        cls.picking = cls.env['stock.picking'].create({
            'name': 'PICK-XLSX-TEST',
            'partner_id': cls.partner.id,
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': destination_location.id,
            'origin': 'SO-XLSX-TEST',
            'move_ids': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 3.0,
                'uom_id': cls.product.uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': destination_location.id,
            })],
        })


    def _assert_report_action(self, record, model, report_name):

        action = record.with_context(active_ids=record.ids).print_excel_report()

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(action['data']['model'], model)
        self.assertEqual(action['data']['output_format'], 'xlsx')
        self.assertEqual(action['data']['report_name'], report_name)
        self.assertEqual(json.loads(action['data']['options']), record.ids)


    def _assert_xlsx_contains(self, record, expected_strings):
        response = XLSXResponse()
        record.get_xlsx_report(record.ids, response)
        response.stream.seek(0)

        self.assertGreater(len(response.stream.getvalue()), 0)
        with zipfile.ZipFile(response.stream) as workbook:
            workbook_files = workbook.namelist()
            self.assertIn('xl/workbook.xml', workbook_files)
            shared_strings = workbook.read('xl/sharedStrings.xml').decode()

        for expected_string in expected_strings:
            self.assertIn(expected_string, shared_strings)

    def test_sale_order_report_action(self):
        """Sale order action returns XLSX report metadata."""
        self._assert_report_action(
            self.sale_order,
            'sale.order',
            'Sale/Quotation Excel Report'
        )


    def test_invoice_report_action(self):
        """Invoice action returns XLSX report metadata."""
        self._assert_report_action(
            self.invoice,
            'account.move',
            'Invoice Excel Report'
        )

    def test_picking_report_action(self):
        """Picking action returns XLSX report metadata."""
        self._assert_report_action(
            self.picking,
            'stock.picking',
            'Picking Order Excel Report'
        )

    def test_sale_order_xlsx_report_content(self):
        """Sale order XLSX contains the expected header and line data."""
        self._assert_xlsx_contains(self.sale_order, [
            'SALE ORDER - %s' % self.sale_order.name,
            'Customer Name',
            'Excel Sale Line',
            'Total Amount',
        ])

    def test_invoice_xlsx_report_content(self):
        """Invoice XLSX contains the expected header and line data."""
        self._assert_xlsx_contains(self.invoice, [
            'INVOICE - %s' % self.invoice.name,
            'Customer/Vendor Name',
            'Excel Invoice Line',
            'Total Amount',
        ])


    def test_picking_xlsx_report_content(self):
        """Picking XLSX contains the expected header and move data."""
        self._assert_xlsx_contains(self.picking, [
            'Delivery - %s' % self.picking.name,
            'Customer/Vendor Name',
            'SO-XLSX-TEST',
        ])

    def test_controller_get_report_xlsx_success(self):
        """Controller successfully returns XLSX stream response."""
        controller = XLSXReportController()
        mock_request = MagicMock()
        mock_request.session.uid = self.env.user.id
        mock_request.env = self.env

        class DummyResponse(Response):
            default_mimetype = None

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.cookies = {}

            def set_cookie(self, key, value='', **kwargs):
                self.cookies[key] = value

        dummy_response = DummyResponse()
        mock_request.make_response.return_value = dummy_response

        with patch('odoo.addons.advanced_excel_reports.controllers.advanced_excel_reports.request', mock_request):
            response = controller.get_report_xlsx(
                model='sale.order',
                options=json.dumps(self.sale_order.ids),
                output_format='xlsx',
                report_name='SaleReport',
                token='token123',
            )
            self.assertEqual(response.status_code, 200)
            mock_request.make_response.assert_called_once()
            headers = dict(mock_request.make_response.call_args[1]['headers'])
            self.assertEqual(headers.get('Content-Type'), 'application/vnd.ms-excel')
            self.assertIn('SaleReport.xlsx', headers.get('Content-Disposition', ''))
            self.assertGreater(len(dummy_response.get_data()), 0)

    def test_controller_get_report_xlsx_error(self):
        """Controller catches exceptions and returns JSON error response."""
        controller = XLSXReportController()
        mock_request = MagicMock()
        mock_request.session.uid = self.env.user.id
        mock_request.env = self.env
        mock_request.make_response.side_effect = lambda data, **kwargs: Response(data)

        with patch('odoo.addons.advanced_excel_reports.controllers.advanced_excel_reports.request', mock_request):
            with patch.object(type(self.sale_order), 'get_xlsx_report', side_effect=Exception('Test Error')):
                result = controller.get_report_xlsx(
                    model='sale.order',
                    options=json.dumps(self.sale_order.ids),
                    output_format='xlsx',
                    report_name='ErrorReport',
                )
                self.assertIn('Odoo Server Error', result.get_data(as_text=True))


