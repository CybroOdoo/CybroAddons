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
from types import SimpleNamespace
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestOutOfStockReport(TransactionCase):
    """Test cases for wizard/out_of_stock_report.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1
        )
        cls.internal_loc = cls.warehouse.lot_stock_id

        cls.parent_categ = cls.env['product.category'].create({'name': 'OOS Parent Cat'})
        cls.child_categ = cls.env['product.category'].create({
            'name': 'OOS Child Cat',
            'parent_id': cls.parent_categ.id,
        })
        cls.in_stock_categ = cls.env['product.category'].create({'name': 'In Stock Cat'})

        cls.product_oos = cls.env['product.product'].create({
            'name': 'OOS Product',
            'default_code': 'OOS-001',
            'is_storable': True,
            'categ_id': cls.child_categ.id,
        })
        cls.product_in_stock = cls.env['product.product'].create({
            'name': 'In Stock Product',
            'default_code': 'INS-001',
            'is_storable': True,
            'categ_id': cls.in_stock_categ.id,
        })
        cls.product_non_storable = cls.env['product.product'].create({
            'name': 'Non Storable Product',
            'is_storable': False,
            'categ_id': cls.child_categ.id,
        })

        cls.env['stock.quant']._update_available_quantity(
            cls.product_in_stock, cls.internal_loc, 10.0
        )

    def test_fetch_out_of_stock_products(self):
        """_fetch_out_of_stock_products returns storable zero-qty products matching filters."""
        wizard = self.env['out.of.stock.report'].create({
            'product_category_id': self.parent_categ.id,
            'company_id': self.env.company.id,
        })
        rows = wizard._fetch_out_of_stock_products()
        names = [row['name'] for row in rows]
        self.assertIn(self.product_oos.name, names)
        self.assertNotIn(self.product_non_storable.name, names)
        self.assertNotIn(self.product_in_stock.name, names)

        wizard_specific = self.env['out.of.stock.report'].create({
            'product_id': self.product_oos.id,
            'company_id': self.env.company.id,
        })
        rows_specific = wizard_specific._fetch_out_of_stock_products()
        self.assertEqual(len(rows_specific), 1)
        self.assertEqual(rows_specific[0]['default_code'], 'OOS-001')
        self.assertEqual(rows_specific[0]['company_name'], self.env.company.name)

    def test_action_print_pdf_report_no_data_raises(self):
        """action_print_pdf_report raises ValidationError when no out-of-stock products match."""
        wizard = self.env['out.of.stock.report'].create({
            'product_id': self.product_in_stock.id,
            'product_category_id': self.in_stock_categ.id,
            'company_id': self.env.company.id,
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_pdf_report()

    def test_action_print_pdf_report_success(self):
        """action_print_pdf_report returns the PDF report action with product_stock data."""
        wizard = self.env['out.of.stock.report'].create({
            'product_id': self.product_oos.id,
            'product_category_id': self.parent_categ.id,
            'company_id': self.env.company.id,
        })
        pdf_action = wizard.with_context(discard_logo_check=True).action_print_pdf_report()
        self.assertEqual(pdf_action['type'], 'ir.actions.report')
        self.assertEqual(
            pdf_action['report_name'],
            'report_stock_inventory.report_out_of_stock',
        )
        self.assertEqual(len(pdf_action['data']['product_stock']), 1)

    def test_action_print_xls_report_no_data_raises(self):
        """action_print_xls_report raises ValidationError when no out-of-stock products match."""
        wizard = self.env['out.of.stock.report'].create({
            'product_id': self.product_in_stock.id,
            'product_category_id': self.in_stock_categ.id,
            'company_id': self.env.company.id,
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_xls_report()

    def test_action_print_xls_report_success(self):
        """action_print_xls_report returns the XLSX report action payload."""
        wizard = self.env['out.of.stock.report'].create({
            'product_id': self.product_oos.id,
            'product_category_id': self.parent_categ.id,
            'company_id': self.env.company.id,
        })
        xls_action = wizard.action_print_xls_report()
        self.assertEqual(xls_action['type'], 'ir.actions.report')
        self.assertEqual(xls_action['report_type'], 'xlsx')
        self.assertEqual(xls_action['data']['model'], 'out.of.stock.report')
        options = json.loads(xls_action['data']['options'])
        self.assertEqual(len(options['product_stock']), 1)

    def test_get_xlsx_report(self):
        """get_xlsx_report writes a valid XLSX workbook to the response stream."""
        wizard = self.env['out.of.stock.report'].create({
            'product_id': self.product_oos.id,
            'product_category_id': self.parent_categ.id,
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
            self.assertIn('OUT OF STOCK REPORT', shared)
            self.assertIn(self.product_oos.name, shared)
