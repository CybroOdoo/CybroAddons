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
class TestStockMoveReport(TransactionCase):
    """Test stock.move.report wizard methods and queries."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for stock move report wizard."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.category = cls.env['product.category'].create({
            'name': 'Stock Move Test Category',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Stock Move Test Product',
            'categ_id': cls.category.id,
        })
        cls.location = cls.env['stock.location'].create({
            'name': 'Stock Move Test Location',
            'usage': 'internal',
        })
        cls.location_dest = cls.env['stock.location'].create({
            'name': 'Stock Move Dest Test Location',
            'usage': 'internal',
        })

    def _create_move(self, product, date, qty=5.0, state='done'):
        """Helper to create a stock.move record."""
        return self.env['stock.move'].create({
            'description_picking': 'Test Stock Move',
            'product_id': product.id,
            'product_uom_qty': qty,
            'location_id': self.location.id,
            'location_dest_id': self.location_dest.id,
            'company_id': self.company.id,
            'date': date,
            'state': state,
        })

    def test_check_date_range(self):
        """Test date validation constraints."""
        now = datetime.now()
        wiz = self.env['stock.move.report'].create({
            'from_date': now - timedelta(days=2),
            'to_date': now,
        })
        wiz._check_date_range()

        with self.assertRaises(ValidationError):
            self.env['stock.move.report'].create({
                'from_date': now,
                'to_date': now - timedelta(days=1),
            })

    def test_get_stock_moves_with_category(self):
        """Test SQL extraction with category filter."""
        now = datetime.now()
        self._create_move(self.product, now, qty=10.0)

        wiz = self.env['stock.move.report'].create({
            'product_category_id': self.category.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'company_id': self.company.id,
            'from_date': now - timedelta(days=1),
            'to_date': now + timedelta(days=1),
        })
        res = wiz._get_stock_moves()
        self.assertTrue(len(res) >= 1)
        self.assertEqual(res[0]['product_name'], 'Stock Move Test Product')
        self.assertEqual(res[0]['category_name'], 'Stock Move Test Category')
        self.assertEqual(res[0]['product_uom_qty'], 10.0)
        self.assertEqual(res[0]['state'], 'done')

    def test_get_stock_moves_without_category(self):
        """Test SQL extraction without category filter and with single date filter."""
        now = datetime.now()
        self._create_move(self.product, now, qty=10.0)

        wiz = self.env['stock.move.report'].create({
            'product_id': self.product.id,
            'company_id': self.company.id,
            'from_date': now,
            'to_date': now,
        })
        res = wiz._get_stock_moves()
        self.assertTrue(len(res) >= 1)
        self.assertEqual(res[0]['product_name'], 'Stock Move Test Product')
        self.assertEqual(res[0]['product_uom_qty'], 10.0)

        wiz_from_only = self.env['stock.move.report'].create({
            'product_id': self.product.id,
            'company_id': self.company.id,
            'from_date': now - timedelta(days=5),
            'to_date': False,
        })
        res_from = wiz_from_only._get_stock_moves()
        self.assertTrue(len(res_from) >= 1)
        self.assertEqual(res_from[0]['product_name'], 'Stock Move Test Product')

        wiz_to_only = self.env['stock.move.report'].create({
            'product_id': self.product.id,
            'company_id': self.company.id,
            'from_date': False,
            'to_date': now + timedelta(days=5),
        })
        res_to = wiz_to_only._get_stock_moves()
        self.assertTrue(len(res_to) >= 1)
        self.assertEqual(res_to[0]['product_name'], 'Stock Move Test Product')

    def test_actions_and_xlsx_generation(self):
        """Test PDF, XLS actions and Excel binary output."""
        wiz = self.env['stock.move.report'].create({
            'product_id': self.product.id,
        })

        pdf_act = wiz.action_print_pdf_report()
        self.assertIn(pdf_act.get('type'), ['ir.actions.report', 'ir.actions.act_window'])

        xls_act = wiz.action_print_xls_report()
        self.assertEqual(xls_act.get('report_type'), 'xlsx')

        data = {
            'company_name': self.company.name,
            'stock_move': [
                {
                    'date': '2026-10-19 12:00:00',
                    'reference': 'WH/OUT/0001',
                    'product_name': 'Test Product',
                    'location_name': 'WH/Stock',
                    'product_uom_qty': 10.0,
                    'name': self.company.name,
                    'category_name': 'Test Category',
                    'state': 'done',
                }
            ],
        }
        dummy_resp = DummyResponse()
        wiz.get_xlsx_report(data, dummy_resp)
        data_bytes = dummy_resp.stream.getvalue()
        self.assertTrue(len(data_bytes) > 0)
        self.assertTrue(data_bytes.startswith(b'PK\x03\x04'))
