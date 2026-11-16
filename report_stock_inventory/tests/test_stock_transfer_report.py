# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (
#    OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
#############################################################################
import io
import json
import zipfile
from datetime import timedelta
from types import SimpleNamespace
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestStockTransferReport(TransactionCase):
    """Test cases for wizard/stock_transfer_report.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1
        )
        cls.internal_loc = cls.warehouse.lot_stock_id
        cls.customer_loc = cls.env.ref('stock.stock_location_customers')
        cls.picking_type = cls.warehouse.out_type_id

        cls.partner = cls.env['res.partner'].create({'name': 'Transfer Test Customer'})
        cls.parent_categ = cls.env['product.category'].create({'name': 'Transfer Parent Cat'})
        cls.child_categ = cls.env['product.category'].create({
            'name': 'Transfer Child Cat',
            'parent_id': cls.parent_categ.id,
        })
        cls.empty_categ = cls.env['product.category'].create({'name': 'Transfer Empty Cat'})

        cls.product = cls.env['product.product'].create({
            'name': 'Transfer Test Product',
            'is_storable': True,
            'categ_id': cls.child_categ.id,
        })

        cls.now = fields.Datetime.now()
        cls.picking = cls.env['stock.picking'].create({
            'partner_id': cls.partner.id,
            'picking_type_id': cls.picking_type.id,
            'location_id': cls.internal_loc.id,
            'location_dest_id': cls.customer_loc.id,
            'scheduled_date': cls.now - timedelta(days=2),
            'origin': 'SO-TRANSFER-001',
            'move_ids': [Command.create({
                'product_id': cls.product.id,
                'product_uom_qty': 4.0,
                'uom_id': cls.product.uom_id.id,
                'location_id': cls.internal_loc.id,
                'location_dest_id': cls.customer_loc.id,
            })],
        })
        cls.picking.action_confirm()

        # Standalone move without picking_id must be ignored
        cls.env['stock.move'].create({
            'product_id': cls.product.id,
            'product_uom_qty': 2.0,
            'uom_id': cls.product.uom_id.id,
            'location_id': cls.internal_loc.id,
            'location_dest_id': cls.customer_loc.id,
        })

    def test_check_dates(self):
        """_check_dates raises ValidationError when from_date > to_date and allows valid range."""
        wizard = self.env['stock.transfer.report'].create({
            'product_category_id': self.parent_categ.id,
            'from_date': self.now - timedelta(days=5),
            'to_date': self.now,
        })
        wizard._check_dates()

        with self.assertRaises(ValidationError):
            self.env['stock.transfer.report'].create({
                'product_category_id': self.parent_categ.id,
                'from_date': self.now + timedelta(days=5),
                'to_date': self.now,
            })

    def test_fetch_stock_transfer_rows(self):
        """_fetch_stock_transfer_rows filters accurately and ignores moves without picking."""
        wizard = self.env['stock.transfer.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'location_id': self.internal_loc.id,
            'picking_type_id': self.picking_type.id,
            'partner_id': self.partner.id,
            'from_date': self.now - timedelta(days=5),
            'to_date': self.now,
            'company_id': self.env.company.id,
        })
        rows = wizard._fetch_stock_transfer_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['picking_name'], self.picking.name)
        self.assertEqual(rows[0]['product_name'], self.product.name)
        self.assertEqual(rows[0]['origin'], 'SO-TRANSFER-001')
        self.assertEqual(rows[0]['company_name'], self.env.company.name)

    def test_action_print_pdf_report_no_data_raises(self):
        """action_print_pdf_report raises ValidationError when no transfer rows match."""
        wizard = self.env['stock.transfer.report'].create({
            'product_category_id': self.empty_categ.id,
            'from_date': self.now - timedelta(days=5),
            'to_date': self.now,
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_pdf_report()

    def test_action_print_pdf_report_success(self):
        """action_print_pdf_report returns the PDF report action with stock_picking rows."""
        wizard = self.env['stock.transfer.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'location_id': self.internal_loc.id,
            'from_date': self.now - timedelta(days=5),
            'to_date': self.now,
            'company_id': self.env.company.id,
        })
        pdf_action = wizard.with_context(discard_logo_check=True).action_print_pdf_report()
        self.assertEqual(pdf_action['type'], 'ir.actions.report')
        self.assertEqual(
            pdf_action['report_name'],
            'report_stock_inventory.report_stock_transfer',
        )
        self.assertEqual(len(pdf_action['data']['stock_picking']), 1)

    def test_action_print_xls_report_no_data_raises(self):
        """action_print_xls_report raises ValidationError when no transfer rows match."""
        wizard = self.env['stock.transfer.report'].create({
            'product_category_id': self.empty_categ.id,
            'from_date': self.now - timedelta(days=5),
            'to_date': self.now,
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_xls_report()

    def test_action_print_xls_report_success(self):
        """action_print_xls_report returns the XLSX report action payload."""
        wizard = self.env['stock.transfer.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'location_id': self.internal_loc.id,
            'from_date': self.now - timedelta(days=5),
            'to_date': self.now,
            'company_id': self.env.company.id,
        })
        xls_action = wizard.action_print_xls_report()
        self.assertEqual(xls_action['type'], 'ir.actions.report')
        self.assertEqual(xls_action['report_type'], 'xlsx')
        self.assertEqual(xls_action['data']['model'], 'stock.transfer.report')
        options = json.loads(xls_action['data']['options'])
        self.assertEqual(len(options['stock_picking']), 1)

    def test_get_xlsx_report(self):
        """get_xlsx_report writes a valid XLSX workbook to the response stream."""
        wizard = self.env['stock.transfer.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'location_id': self.internal_loc.id,
            'from_date': self.now - timedelta(days=5),
            'to_date': self.now,
            'company_id': self.env.company.id,
        })
        xls_action = wizard.action_print_xls_report()
        options = json.loads(xls_action['data']['options'])

        stream = io.BytesIO()
        wizard.get_xlsx_report(options, SimpleNamespace(stream=stream))
        stream.seek(0)
        with zipfile.ZipFile(stream) as zf:
            self.assertIn('xl/worksheets/sheet1.xml', zf.namelist())
            shared = zf.read('xl/sharedStrings.xml').decode('utf-8')
            self.assertIn('STOCK TRANSFER REPORT', shared)
            self.assertIn(self.picking.name, shared)
