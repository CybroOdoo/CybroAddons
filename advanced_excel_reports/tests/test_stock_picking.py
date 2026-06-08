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
    """Minimal response object used by stock.picking XLSX report tests."""

    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestStockPickingExcelReport(TransactionCase):
    """Test stock.picking XLSX report action and workbook content."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Stock Picking XLSX Partner',
            'street': 'Picking Street',
            'zip': '24680',
            'phone': '555-0144',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Stock Picking XLSX Product',
            'list_price': 90.0,
            'standard_price': 30.0,
        })

        cls.picking_type = cls.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', 'in', [False, cls.env.company.id]),
        ], limit=1)
        if not cls.picking_type:
            raise AssertionError("An outgoing picking type is required.")

        cls.source_location = (
            cls.picking_type.default_location_src_id
            or cls.env.ref('stock.stock_location_stock')
        )
        cls.destination_location = (
            cls.picking_type.default_location_dest_id
            or cls.env.ref('stock.stock_location_customers')
        )


        cls.picking = cls.env['stock.picking'].create({
            'name': 'PICK-XLSX-CASE',
            'partner_id': cls.partner.id,
            'picking_type_id': cls.picking_type.id,
            'location_id': cls.source_location.id,
            'location_dest_id': cls.destination_location.id,
            'origin': 'PICK-XLSX-REF',
            'move_ids': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 4.0,
                'product_uom': cls.product.uom_id.id,
                'location_id': cls.source_location.id,
                'location_dest_id': cls.destination_location.id,
            })],
        })



    def _get_xlsx_shared_strings(self, picking):

        response = XLSXResponse()
        picking.get_xlsx_report(picking.ids, response)
        response.stream.seek(0)
        self.assertGreater(len(response.stream.getvalue()), 0)

        with zipfile.ZipFile(response.stream) as workbook:

            self.assertIn('xl/workbook.xml', workbook.namelist())
            shared_strings = workbook.read('xl/sharedStrings.xml').decode()
            return shared_strings

    def test_print_excel_report_action(self):
        """print_excel_report returns the expected XLSX action payload."""
        action = self.picking.with_context(
            active_ids=self.picking.ids
        ).print_excel_report()

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(action['data']['model'], 'stock.picking')
        self.assertEqual(action['data']['output_format'], 'xlsx')
        self.assertEqual(
            action['data']['report_name'],
            'Picking Order Excel Report'
        )
        self.assertEqual(
            json.loads(action['data']['options']),
            self.picking.ids
        )


    def test_get_xlsx_report_content(self):
        """get_xlsx_report writes picking header and move values."""
        shared_strings = self._get_xlsx_shared_strings(self.picking)

        expected_values = [
            'Delivery - %s' % self.picking.name,
            'Company Name : %s' % self.env.company.name,
            'Customer/Vendor Name',
            self.partner.name,
            self.partner.street,
            self.partner.zip,
            self.partner.phone,
            'Scheduled Date',
            'Effective Date',
            'Operation Type',
            self.picking_type.display_name,
            'Source Location',
            self.source_location.complete_name,
            'Destination Location',
            self.destination_location.complete_name,
            'State',
            'Responsible Person',
            'Source Document',
            'PICK-XLSX-REF',
            'Product',
            'Description',
            'Deadline',
            'Quantity',
            'Quantity Done',
            self.product.name,
        ]


        for value in expected_values:
            self.assertIn(value, shared_strings)
