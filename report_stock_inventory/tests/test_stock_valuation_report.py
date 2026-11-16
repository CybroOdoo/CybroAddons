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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestStockValuationReport(TransactionCase):
    """Test cases for wizard/stock_valuation_report.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1
        )
        cls.internal_loc = cls.warehouse.lot_stock_id
        cls.supplier_loc = cls.env.ref('stock.stock_location_suppliers')

        cls.parent_categ = cls.env['product.category'].create({
            'name': 'Valuation Parent Cat',
            'property_cost_method': 'standard',
        })
        cls.child_categ = cls.env['product.category'].create({
            'name': 'Valuation Child Cat',
            'parent_id': cls.parent_categ.id,
            'property_cost_method': 'standard',
        })
        cls.empty_categ = cls.env['product.category'].create({'name': 'Valuation Empty Cat'})

        cls.product = cls.env['product.product'].create({
            'name': 'Valuated Test Product',
            'default_code': 'VAL-001',
            'is_storable': True,
            'standard_price': 25.0,
            'categ_id': cls.child_categ.id,
        })

        cls.move = cls.env['stock.move'].create({
            'product_id': cls.product.id,
            'product_uom_qty': 4.0,
            'uom_id': cls.product.uom_id.id,
            'location_id': cls.supplier_loc.id,
            'location_dest_id': cls.internal_loc.id,
            'price_unit': 25.0,
        })
        cls.move._action_confirm()
        cls.move.quantity = 4.0
        cls.move.picked = True
        cls.move._action_done()

        cls.now = fields.Datetime.now()

    def test_check_dates(self):
        """_check_dates raises ValidationError when from_Date > to_date and allows valid range."""
        wizard = self.env['stock.valuation.report'].create({
            'product_category_id': self.parent_categ.id,
            'from_Date': self.now - timedelta(days=1),
            'to_date': self.now + timedelta(days=1),
        })
        wizard._check_dates()

        with self.assertRaises(ValidationError):
            self.env['stock.valuation.report'].create({
                'product_category_id': self.parent_categ.id,
                'from_Date': self.now + timedelta(days=5),
                'to_date': self.now,
            })

    def test_fetch_valuation_rows(self):
        """_fetch_valuation_rows returns done valued stock moves matching filters."""
        wizard = self.env['stock.valuation.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'from_Date': self.now - timedelta(days=1),
            'to_date': self.now + timedelta(days=1),
            'company_id': self.env.company.id,
        })
        rows = wizard._fetch_valuation_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['product_ref'], 'VAL-001')
        self.assertEqual(rows[0]['name'], self.product.name)
        self.assertEqual(rows[0]['complete_name'], self.child_categ.complete_name)
        self.assertEqual(rows[0]['quantity'], 4.0)
        self.assertEqual(rows[0]['unit_cost'], 25.0)
        self.assertEqual(rows[0]['value'], 100.0)

    def test_action_print_pdf_report_no_data_raises(self):
        """action_print_pdf_report raises ValidationError when no valuation rows match."""
        wizard = self.env['stock.valuation.report'].create({
            'product_category_id': self.empty_categ.id,
            'from_Date': self.now - timedelta(days=1),
            'to_date': self.now + timedelta(days=1),
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_pdf_report()

    def test_action_print_pdf_report_success(self):
        """action_print_pdf_report returns the PDF report action with stock_valuation rows."""
        wizard = self.env['stock.valuation.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'from_Date': self.now - timedelta(days=1),
            'to_date': self.now + timedelta(days=1),
            'company_id': self.env.company.id,
        })
        pdf_action = wizard.with_context(discard_logo_check=True).action_print_pdf_report()
        self.assertEqual(pdf_action['type'], 'ir.actions.report')
        self.assertEqual(
            pdf_action['report_name'],
            'report_stock_inventory.report_stock_valuation',
        )
        self.assertEqual(len(pdf_action['data']['stock_valuation']), 1)

    def test_action_print_xls_report_no_data_raises(self):
        """action_print_xls_report raises ValidationError when no valuation rows match."""
        wizard = self.env['stock.valuation.report'].create({
            'product_category_id': self.empty_categ.id,
            'from_Date': self.now - timedelta(days=1),
            'to_date': self.now + timedelta(days=1),
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_xls_report()

    def test_action_print_xls_report_success(self):
        """action_print_xls_report returns the XLSX report action payload."""
        wizard = self.env['stock.valuation.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'from_Date': self.now - timedelta(days=1),
            'to_date': self.now + timedelta(days=1),
            'company_id': self.env.company.id,
        })
        xls_action = wizard.action_print_xls_report()
        self.assertEqual(xls_action['type'], 'ir.actions.report')
        self.assertEqual(xls_action['report_type'], 'xlsx')
        self.assertEqual(xls_action['data']['model'], 'stock.valuation.report')
        options = json.loads(xls_action['data']['options'])
        self.assertEqual(len(options['stock_valuation']), 1)

    def test_get_xlsx_report(self):
        """get_xlsx_report writes a valid XLSX workbook to the response stream."""
        wizard = self.env['stock.valuation.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'from_Date': self.now - timedelta(days=1),
            'to_date': self.now + timedelta(days=1),
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
            self.assertIn('STOCK VALUATION REPORT', shared)
            self.assertIn('VAL-001', shared)
