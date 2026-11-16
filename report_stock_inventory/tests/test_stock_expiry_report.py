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
class TestStockExpiryReport(TransactionCase):
    """Test cases for wizard/stock_expiry_report.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1
        )
        cls.internal_loc = cls.warehouse.lot_stock_id

        cls.parent_categ = cls.env['product.category'].create({'name': 'Expiry Parent Cat'})
        cls.child_categ = cls.env['product.category'].create({
            'name': 'Expiry Child Cat',
            'parent_id': cls.parent_categ.id,
        })
        cls.empty_categ = cls.env['product.category'].create({'name': 'Expiry Empty Cat'})

        cls.product = cls.env['product.product'].create({
            'name': 'Expiring Product',
            'is_storable': True,
            'tracking': 'lot',
            'use_expiration_date': True,
            'categ_id': cls.child_categ.id,
        })

        cls.now = fields.Datetime.now()
        cls.lot_in_range = cls.env['stock.lot'].create({
            'name': 'LOT-EXP-01',
            'product_id': cls.product.id,
            'company_id': cls.env.company.id,
            'expiration_date': cls.now + timedelta(days=5),
        })
        cls.lot_out_of_range = cls.env['stock.lot'].create({
            'name': 'LOT-EXP-02',
            'product_id': cls.product.id,
            'company_id': cls.env.company.id,
            'expiration_date': cls.now + timedelta(days=40),
        })

        cls.env['stock.quant']._update_available_quantity(
            cls.product, cls.internal_loc, 12.0, lot_id=cls.lot_in_range
        )
        cls.env['stock.quant']._update_available_quantity(
            cls.product, cls.internal_loc, 6.0, lot_id=cls.lot_out_of_range
        )

    def test_check_dates(self):
        """_check_dates raises ValidationError when from_date > to_date and allows valid range."""
        wizard = self.env['stock.expiry.report'].create({
            'product_category_id': self.parent_categ.id,
            'from_date': self.now,
            'to_date': self.now + timedelta(days=10),
        })
        wizard._check_dates()

        with self.assertRaises(ValidationError):
            self.env['stock.expiry.report'].create({
                'product_category_id': self.parent_categ.id,
                'from_date': self.now + timedelta(days=10),
                'to_date': self.now,
            })

    def test_fetch_stock_expiry_rows(self):
        """_fetch_stock_expiry_rows matches child category lots within expiration window."""
        self.env.flush_all()
        wizard = self.env['stock.expiry.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'from_date': self.now,
            'to_date': self.now + timedelta(days=15),
            'company_id': self.env.company.id,
        })
        rows = wizard._fetch_stock_expiry_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['sl_no'], 'LOT-EXP-01')
        self.assertEqual(rows[0]['quantity'], 12.0)
        self.assertEqual(rows[0]['complete_name'], self.child_categ.complete_name)
        self.assertEqual(rows[0]['company_name'], self.env.company.name)

    def test_action_print_pdf_report_no_data_raises(self):
        """action_print_pdf_report raises ValidationError when no expiry rows match."""
        self.env.flush_all()
        wizard = self.env['stock.expiry.report'].create({
            'product_category_id': self.empty_categ.id,
            'from_date': self.now,
            'to_date': self.now + timedelta(days=15),
            'company_id': self.env.company.id,
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_pdf_report()

    def test_action_print_pdf_report_success(self):
        """action_print_pdf_report returns the PDF report action with expiry rows."""
        self.env.flush_all()
        wizard = self.env['stock.expiry.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'from_date': self.now,
            'to_date': self.now + timedelta(days=15),
            'company_id': self.env.company.id,
        })
        pdf_action = wizard.with_context(discard_logo_check=True).action_print_pdf_report()
        self.assertEqual(pdf_action['type'], 'ir.actions.report')
        self.assertEqual(
            pdf_action['report_name'],
            'report_stock_inventory.report_stock_expiry',
        )
        self.assertEqual(len(pdf_action['data']['stock_expiry']), 1)

    def test_action_print_xls_report_no_data_raises(self):
        """action_print_xls_report raises ValidationError when no expiry rows match."""
        self.env.flush_all()
        wizard = self.env['stock.expiry.report'].create({
            'product_category_id': self.empty_categ.id,
            'from_date': self.now,
            'to_date': self.now + timedelta(days=15),
            'company_id': self.env.company.id,
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_xls_report()

    def test_action_print_xls_report_success(self):
        """action_print_xls_report returns the XLSX report action payload."""
        self.env.flush_all()
        wizard = self.env['stock.expiry.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'from_date': self.now,
            'to_date': self.now + timedelta(days=15),
            'company_id': self.env.company.id,
        })
        xls_action = wizard.action_print_xls_report()
        self.assertEqual(xls_action['type'], 'ir.actions.report')
        self.assertEqual(xls_action['report_type'], 'xlsx')
        self.assertEqual(xls_action['data']['model'], 'stock.expiry.report')
        options = json.loads(xls_action['data']['options'])
        self.assertEqual(len(options['stock_expiry']), 1)

    def test_get_xlsx_report(self):
        """get_xlsx_report writes a valid XLSX workbook to the response stream."""
        self.env.flush_all()
        wizard = self.env['stock.expiry.report'].create({
            'product_category_id': self.parent_categ.id,
            'product_id': self.product.id,
            'from_date': self.now,
            'to_date': self.now + timedelta(days=15),
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
            self.assertIn('STOCK EXPIRY REPORT', shared)
            self.assertIn('LOT-EXP-01', shared)
