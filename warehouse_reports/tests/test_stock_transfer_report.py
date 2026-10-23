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
#############################################################################
from datetime import datetime, timedelta
import io

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


class DummyResponse:
    """Helper response container with stream attribute."""

    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestStockTransferReport(TransactionCase):
    """Test stock.transfer.report wizard methods and queries."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for stock transfer report wizard."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Stock Transfer Test Partner',
        })
        cls.category = cls.env['product.category'].create({
            'name': 'Stock Transfer Test Category',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Stock Transfer Test Product',
            'categ_id': cls.category.id,
        })
        cls.location = cls.env['stock.location'].create({
            'name': 'Stock Transfer Test Location',
            'usage': 'internal',
        })
        cls.location_dest = cls.env['stock.location'].create({
            'name': 'Stock Transfer Dest Location',
            'usage': 'internal',
        })
        cls.picking_type = cls.env['stock.picking.type'].search([
            ('warehouse_id.company_id', '=', cls.company.id)
        ], limit=1)
        if not cls.picking_type:
            cls.picking_type = cls.env['stock.picking.type'].create({
                'name': 'Test Picking Type',
                'code': 'internal',
                'sequence_code': 'TPICK',
            })

    def _create_picking_with_move(self, scheduled_date):
        """Helper to create a stock.picking with stock.move."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type.id,
            'location_id': self.location.id,
            'location_dest_id': self.location_dest.id,
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'scheduled_date': scheduled_date,
        })
        self.env['stock.move'].create({
            'description_picking': 'Transfer Move',
            'product_id': self.product.id,
            'product_uom_qty': 10.0,
            'location_id': self.location.id,
            'location_dest_id': self.location_dest.id,
            'picking_id': picking.id,
            'company_id': self.company.id,
        })
        return picking

    def test_check_date_range(self):
        """Test date validation constraints."""
        now = datetime.now()
        wiz = self.env['stock.transfer.report'].create({
            'from_date': now - timedelta(days=2),
            'to_date': now,
        })
        wiz._check_date_range()

        with self.assertRaises(ValidationError):
            self.env['stock.transfer.report'].create({
                'from_date': now,
                'to_date': now - timedelta(days=1),
            })

    def test_get_stock_transfers_with_category(self):
        """Test SQL query for stock transfers with category filter."""
        now = datetime.now()
        picking = self._create_picking_with_move(now)

        wiz = self.env['stock.transfer.report'].create({
            'product_category_id': self.category.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'picking_type_id': self.picking_type.id,
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'from_date': now - timedelta(days=1),
            'to_date': now + timedelta(days=1),
        })
        res = wiz._get_stock_transfers()
        self.assertTrue(len(res) >= 1)
        found = next((r for r in res if r.get('picking_name') == picking.name), None)
        self.assertIsNotNone(found)
        self.assertEqual(found.get('product_name'), 'Stock Transfer Test Product')
        self.assertEqual(found.get('category_name'), 'Stock Transfer Test Category')
        self.assertEqual(found.get('company_name'), self.company.name)
        self.assertEqual(found.get('state'), picking.state)
        self.assertEqual(found.get('display_name'), self.picking_type.display_name)

    def test_get_stock_transfers_without_category(self):
        """Test SQL query without category filter and date range variations."""
        now = datetime.now()
        picking = self._create_picking_with_move(now)

        wiz = self.env['stock.transfer.report'].create({
            'product_id': self.product.id,
            'company_id': self.company.id,
            'from_date': now - timedelta(days=1),
            'to_date': now + timedelta(days=1),
        })
        res = wiz._get_stock_transfers()
        self.assertTrue(len(res) >= 1)
        found = next((r for r in res if r.get('picking_name') == picking.name), None)
        self.assertIsNotNone(found)
        self.assertEqual(found.get('product_name'), 'Stock Transfer Test Product')
        self.assertEqual(found.get('state'), picking.state)
        self.assertEqual(found.get('display_name'), self.picking_type.display_name)

        wiz_from_only = self.env['stock.transfer.report'].create({
            'product_id': self.product.id,
            'company_id': self.company.id,
            'from_date': now - timedelta(days=2),
            'to_date': False,
        })
        res_from = wiz_from_only._get_stock_transfers()
        self.assertTrue(len(res_from) >= 1)
        self.assertTrue(any(r.get('picking_name') == picking.name for r in res_from))

        wiz_to_only = self.env['stock.transfer.report'].create({
            'product_id': self.product.id,
            'company_id': self.company.id,
            'from_date': False,
            'to_date': now + timedelta(days=2),
        })
        res_to = wiz_to_only._get_stock_transfers()
        self.assertTrue(len(res_to) >= 1)
        self.assertTrue(any(r.get('picking_name') == picking.name for r in res_to))

    def test_actions_and_xlsx_generation(self):
        """Test PDF, XLS actions and Excel output stream."""
        wiz = self.env['stock.transfer.report'].create({
            'product_id': self.product.id,
        })

        pdf_act = wiz.action_print_pdf_report()
        self.assertIn(pdf_act.get('type'), ['ir.actions.report', 'ir.actions.act_window'])

        xls_act = wiz.action_print_xls_report()
        self.assertEqual(xls_act.get('report_type'), 'xlsx')

        data = {
            'company_name': self.company.name,
            'stock_picking': [
                {
                    'picking_name': 'WH/IN/0001',
                    'product_name': 'Test Product',
                    'scheduled_date': '2026-10-19 10:00:00',
                    'date_deadline': '2026-10-20 10:00:00',
                    'date_done': '2026-10-19 12:00:00',
                    'origin': 'SO001',
                    'complete_name': 'WH/Stock',
                    'display_name': 'Receipts',
                    'company_name': self.company.name,
                    'state': 'done',
                }
            ],
        }
        dummy_resp = DummyResponse()
        wiz.get_xlsx_report(data, dummy_resp)
        data_bytes = dummy_resp.stream.getvalue()
        self.assertTrue(len(data_bytes) > 0)
        self.assertTrue(data_bytes.startswith(b'PK\x03\x04'))
