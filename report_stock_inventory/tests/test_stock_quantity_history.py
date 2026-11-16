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
class TestStockQuantityHistory(TransactionCase):
    """Test cases for wizard/stock_quantity_history.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1
        )
        cls.internal_loc = cls.warehouse.lot_stock_id
        cls.supplier_loc = cls.env.ref('stock.stock_location_suppliers')

        cls.categ = cls.env['product.category'].create({'name': 'History Test Cat'})
        cls.empty_categ = cls.env['product.category'].create({'name': 'History Empty Cat'})

        cls.product = cls.env['product.product'].create({
            'name': 'History Test Product',
            'default_code': 'HIST-01',
            'is_storable': True,
            'categ_id': cls.categ.id,
        })

        cls.now = fields.Datetime.now()
        move = cls.env['stock.move'].create({
            'product_id': cls.product.id,
            'product_uom_qty': 15.0,
            'uom_id': cls.product.uom_id.id,
            'location_id': cls.supplier_loc.id,
            'location_dest_id': cls.internal_loc.id,
        })
        move._action_confirm()
        move.quantity = 15.0
        move.picked = True
        move._action_done()
        move.write({'date': cls.now - timedelta(days=1)})

    def test_action_print_pdf_no_data_raises(self):
        """action_print_pdf raises ValidationError when no stock matches."""
        wizard = self.env['stock.quantity.history'].create({
            'inventory_datetime': self.now,
            'category': [Command.set([self.empty_categ.id])],
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_pdf()

    def test_action_print_pdf_success(self):
        """action_print_pdf returns the PDF report action with location and category metadata."""
        wizard = self.env['stock.quantity.history'].create({
            'inventory_datetime': self.now,
            'location': [Command.set([self.internal_loc.id])],
            'category': [Command.set([self.categ.id])],
        })
        pdf_action = wizard.with_context(discard_logo_check=True).action_print_pdf()
        self.assertEqual(pdf_action['type'], 'ir.actions.report')
        self.assertEqual(
            pdf_action['report_name'],
            'report_stock_inventory.report_stock_pdf',
        )
        self.assertEqual(pdf_action['data']['loc_name'], self.internal_loc.display_name)
        self.assertEqual(pdf_action['data']['categ_name'], self.categ.name)

    def test_action_xlsx_report_no_data_raises(self):
        """action_xlsx_report raises ValidationError when no stock matches."""
        wizard = self.env['stock.quantity.history'].create({
            'inventory_datetime': self.now,
            'category': [Command.set([self.empty_categ.id])],
        })
        with self.assertRaises(ValidationError):
            wizard.action_xlsx_report()

    def test_action_xlsx_report_success(self):
        """action_xlsx_report returns the XLSX report action payload."""
        wizard = self.env['stock.quantity.history'].create({
            'inventory_datetime': self.now,
            'location': [Command.set([self.internal_loc.id])],
            'category': [Command.set([self.categ.id])],
        })
        xls_action = wizard.action_xlsx_report()
        self.assertEqual(xls_action['type'], 'ir.actions.report')
        self.assertEqual(xls_action['report_type'], 'xlsx')
        self.assertEqual(xls_action['data']['model'], 'stock.quantity.history')
        options = json.loads(xls_action['data']['options'])
        self.assertEqual(options['loc_name'], self.internal_loc.display_name)
        self.assertEqual(options['categ_name'], self.categ.name)

    def test_get_xlsx_report(self):
        """get_xlsx_report writes valid XLSX across all location/category header variants."""
        for loc_ids, cat_ids in (
            ([self.internal_loc.id], [self.categ.id]),
            ([self.internal_loc.id], []),
            ([], [self.categ.id]),
        ):
            wizard = self.env['stock.quantity.history'].create({
                'inventory_datetime': self.now,
                'location': [Command.set(loc_ids)],
                'category': [Command.set(cat_ids)],
            })
            xls_action = wizard.action_xlsx_report()
            options = json.loads(xls_action['data']['options'])
            stream = io.BytesIO()
            wizard.get_xlsx_report(options, SimpleNamespace(stream=stream))
            stream.seek(0)
            with zipfile.ZipFile(stream) as zf:
                self.assertIn('xl/worksheets/sheet1.xml', zf.namelist())
                shared = zf.read('xl/sharedStrings.xml').decode('utf-8')
                self.assertIn('Inventory Stock Report', shared)
                self.assertIn(self.product.name, shared)
