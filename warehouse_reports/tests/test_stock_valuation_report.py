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
class TestStockValuationReport(TransactionCase):
    """Test stock.valuation.report wizard methods and queries."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for stock valuation report wizard."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.category = cls.env['product.category'].create({
            'name': 'Stock Val Test Category',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Stock Val Test Product',
            'categ_id': cls.category.id,
            'standard_price': 25.0,
        })
        cls.location = cls.env['stock.location'].create({
            'name': 'Stock Val Test Location',
            'usage': 'internal',
        })
        cls.location_dest = cls.env['stock.location'].create({
            'name': 'Stock Val Dest Location',
            'usage': 'customer',
        })

    def _create_done_move(self, product, date, qty=2.0, price_unit=25.0):
        """Helper to create a done stock.move record."""
        return self.env['stock.move'].create({
            'description_picking': 'Valuation Test Move',
            'product_id': product.id,
            'product_uom_qty': qty,
            'price_unit': price_unit,
            'location_id': self.location.id,
            'location_dest_id': self.location_dest.id,
            'company_id': self.company.id,
            'date': date,
            'state': 'done',
        })

    def test_check_date_range(self):
        """Test date validation constraints."""
        now = datetime.now()
        wiz = self.env['stock.valuation.report'].create({
            'from_date': now - timedelta(days=2),
            'to_date': now,
        })
        wiz._check_date_range()

        with self.assertRaises(ValidationError):
            self.env['stock.valuation.report'].create({
                'from_date': now,
                'to_date': now - timedelta(days=1),
            })

    def test_get_stock_valuations_with_category(self):
        """Test SQL extraction with category filter."""
        now = datetime.now()
        move = self._create_done_move(self.product, now)

        wiz = self.env['stock.valuation.report'].create({
            'product_category_id': self.category.id,
            'product_id': self.product.id,
            'company_id': self.company.id,
            'from_date': now - timedelta(days=1),
            'to_date': now + timedelta(days=1),
        })
        res = wiz._get_stock_valuations()
        self.assertTrue(len(res) >= 1)
        found = next((r for r in res if r.get('move_id') == move.id), None)
        self.assertIsNotNone(found)
        self.assertEqual(found.get('name'), 'Stock Val Test Product')
        self.assertEqual(found.get('category_name'), 'Stock Val Test Category')
        self.assertEqual(found.get('quantity'), 2.0)
        self.assertEqual(found.get('unit_cost'), 25.0)
        self.assertEqual(found.get('value'), 50.0)

    def test_get_stock_valuations_without_category(self):
        """Test SQL extraction without category filter and date edge cases."""
        now = datetime.now()
        move = self._create_done_move(self.product, now)

        wiz = self.env['stock.valuation.report'].create({
            'product_id': self.product.id,
            'company_id': self.company.id,
            'from_date': now - timedelta(days=1),
            'to_date': now + timedelta(days=1),
        })
        res = wiz._get_stock_valuations()
        self.assertTrue(len(res) >= 1)
        found = next((r for r in res if r.get('move_id') == move.id), None)
        self.assertIsNotNone(found)
        self.assertEqual(found.get('name'), 'Stock Val Test Product')
        self.assertEqual(found.get('quantity'), 2.0)
        self.assertEqual(found.get('unit_cost'), 25.0)
        self.assertEqual(found.get('value'), 50.0)

        wiz_from_only = self.env['stock.valuation.report'].create({
            'product_id': self.product.id,
            'company_id': self.company.id,
            'from_date': now - timedelta(days=3),
            'to_date': False,
        })
        res_from = wiz_from_only._get_stock_valuations()
        self.assertTrue(len(res_from) >= 1)
        self.assertTrue(any(r.get('move_id') == move.id for r in res_from))

        wiz_to_only = self.env['stock.valuation.report'].create({
            'product_id': self.product.id,
            'company_id': self.company.id,
            'from_date': False,
            'to_date': now + timedelta(days=3),
        })
        res_to = wiz_to_only._get_stock_valuations()
        self.assertTrue(len(res_to) >= 1)
        self.assertTrue(any(r.get('move_id') == move.id for r in res_to))

    def test_svl_fallback_and_data_enrichment(self):
        """Test stock valuation layer fallback when unit_cost is present."""
        now = datetime.now()
        move = self._create_done_move(self.product, now, qty=4.0, price_unit=25.0)
        if 'stock.valuation.layer' in self.env:
            self.env['stock.valuation.layer'].create({
                'stock_move_id': move.id,
                'product_id': self.product.id,
                'company_id': self.company.id,
                'quantity': 4.0,
                'unit_cost': 30.0,
                'value': 120.0,
            })

        wiz = self.env['stock.valuation.report'].create({
            'product_id': self.product.id,
            'company_id': self.company.id,
            'from_date': now - timedelta(days=1),
            'to_date': now + timedelta(days=1),
        })
        res = wiz._get_stock_valuations()
        found = next((r for r in res if r.get('move_id') == move.id), None)
        if found:
            expected_cost = 30.0 if 'stock.valuation.layer' in self.env else 25.0
            self.assertEqual(found.get('unit_cost'), expected_cost)

    def test_actions_and_xlsx_generation(self):
        """Test PDF, XLS actions and Excel output generation."""
        wiz = self.env['stock.valuation.report'].create({
            'product_id': self.product.id,
        })

        pdf_act = wiz.action_print_pdf_report()
        self.assertIn(pdf_act.get('type'), ['ir.actions.report', 'ir.actions.act_window'])

        xls_act = wiz.action_print_xls_report()
        self.assertEqual(xls_act.get('report_type'), 'xlsx')

        data = {
            'company_name': self.company.name,
            'stock_valuation': [
                {
                    'create_date': '2026-10-19 12:00:00',
                    'name': 'Stock Val Test Product',
                    'description': 'WH/OUT/0002',
                    'category_name': 'Stock Val Test Category',
                    'company_name': self.company.name,
                    'quantity': 2.0,
                    'unit_cost': 25.0,
                    'value': 50.0,
                }
            ],
        }
        dummy_resp = DummyResponse()
        wiz.get_xlsx_report(data, dummy_resp)
        data_bytes = dummy_resp.stream.getvalue()
        self.assertTrue(len(data_bytes) > 0)
        self.assertTrue(data_bytes.startswith(b'PK\x03\x04'))
