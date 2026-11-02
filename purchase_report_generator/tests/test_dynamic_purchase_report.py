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

import io
import json
from datetime import datetime, timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class MockResponse:
    """Mock HTTP response object providing a stream for XLSX generation."""
    def __init__(self):
        self.stream = io.BytesIO()
        self.headers = []
        self.cookies = {}

    def set_cookie(self, key, value):
        self.cookies[key] = value


@tagged('post_install', '-at_install')
class TestDynamicPurchaseReport(TransactionCase):
    """Test suite covering DynamicPurchaseReport model, XLSX generation,
    and QWeb report."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env['dynamic.purchase.report']

        # Setup Partner / Vendor
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Vendor Enterprise',
            'email': 'vendor@example.com',
        })

        # Setup Category
        cls.category = cls.env['product.category'].create({
            'name': 'Test Procurement Category',
        })

        # Setup Products
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Office Laptop Pro',
            'default_code': 'LAP_01',
            'categ_id': cls.category.id,
            'purchase_ok': True,
            'list_price': 1200.0,
            'standard_price': 900.0,
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Wireless Ergonomic Mouse',
            'default_code': 'MOU_02',
            'categ_id': cls.category.id,
            'purchase_ok': True,
            'list_price': 50.0,
            'standard_price': 30.0,
        })

        now = fields.Datetime.now()

        # PO 1: Draft RFQ with HTML note
        cls.po_draft = cls.env['purchase.order'].create({
            'partner_id': cls.vendor.id,
            'user_id': cls.env.user.id,
            'date_order': now - timedelta(days=2),
            'note': '<p>Terms: <b>Immediate delivery</b> requested.</p>',
            'order_line': [
                Command.create({
                    'product_id': cls.product_1.id,
                    'name': cls.product_1.name,
                    'product_qty': 2.0,
                    'price_unit': 900.0,
                    'date_planned': now,
                }),
            ],
        })

        # PO 2: RFQ Sent
        cls.po_sent = cls.env['purchase.order'].create({
            'partner_id': cls.vendor.id,
            'user_id': cls.env.user.id,
            'date_order': now - timedelta(days=1),
            'order_line': [
                Command.create({
                    'product_id': cls.product_2.id,
                    'name': cls.product_2.name,
                    'product_qty': 10.0,
                    'price_unit': 30.0,
                    'date_planned': now,
                }),
            ],
        })
        cls.po_sent.write({'state': 'sent'})

        # PO 3: Confirmed Purchase Order
        cls.po_confirmed = cls.env['purchase.order'].create({
            'partner_id': cls.vendor.id,
            'user_id': cls.env.user.id,
            'date_order': now,
            'order_line': [
                Command.create({
                    'product_id': cls.product_1.id,
                    'name': cls.product_1.name,
                    'product_qty': 5.0,
                    'price_unit': 850.0,
                    'date_planned': now,
                }),
                Command.create({
                    'product_id': cls.product_2.id,
                    'name': cls.product_2.name,
                    'product_qty': 5.0,
                    'price_unit': 28.0,
                    'date_planned': now,
                }),
            ],
        })
        cls.po_confirmed.button_confirm()

    def test_strip_html_tags(self):
        """Test HTML tag removal utility method."""
        self.assertEqual(self.report_model.strip_html_tags(None), '')
        self.assertEqual(self.report_model.strip_html_tags(''), '')
        self.assertEqual(
            self.report_model.strip_html_tags(
                '<p>Hello <b>World</b>! <br/>Sample &amp; test.</p>'
            ),
            'Hello World! Sample &amp; test.'
        )

    def test_get_filter_and_data(self):
        """Test get_filter and get_filter_data for all types."""
        report_types = [
            ('report_by_order', 'Report By Order'),
            ('report_by_order_detail', 'Report By Order Detail'),
            ('report_by_product', 'Report By Product'),
            ('report_by_categories', 'Report By Categories'),
            (
                'report_by_purchase_representative',
                'Report By Purchase Representative',
            ),
            ('report_by_state', 'Report By State'),
        ]
        for r_type, expected_label in report_types:
            record = self.report_model.create({'report_type': r_type})
            filters = self.report_model.get_filter([record.id])
            self.assertEqual(filters.get('report_type'), expected_label)

        # Fallback branch in get_filter
        record_default = self.report_model.create({})
        record_default.report_type = False
        filters_fallback = self.report_model.get_filter([record_default.id])
        self.assertEqual(
            filters_fallback.get('report_type'), 'report_by_order'
        )

    def test_purchase_report_all_types(self):
        """Test purchase_report execution and values for 6 report types."""
        test_po_ids = {
            self.po_draft.id, self.po_sent.id, self.po_confirmed.id
        }

        # 1. Report By Order
        rec_order = self.report_model.create({
            'report_type': 'report_by_order',
        })
        res_order = self.report_model.purchase_report([rec_order.id])
        lines_order = [
            line for line in res_order['report_lines']
            if line.get('id') in test_po_ids
        ]
        self.assertEqual(len(lines_order), 3)
        self.assertEqual(sum(line['sum'] for line in lines_order), 22.0)
        expected_order_total = sum(
            po.amount_total for po in (
                self.po_draft, self.po_sent, self.po_confirmed
            )
        )
        self.assertEqual(
            sum(line['amount_total'] for line in lines_order),
            expected_order_total
        )

        # 2. Report By Order Detail
        rec_detail = self.report_model.create({
            'report_type': 'report_by_order_detail',
        })
        res_detail = self.report_model.purchase_report([rec_detail.id])
        lines_detail = [
            line for line in res_detail['report_lines']
            if line.get('id') in test_po_ids
        ]
        self.assertEqual(len(lines_detail), 4)
        self.assertEqual(sum(line['sum'] for line in lines_detail), 22.0)
        self.assertEqual(
            sum(line['price_subtotal'] for line in lines_detail), 6490.0
        )
        self.assertEqual(
            sum(line['amount_total'] for line in lines_detail), 6490.0
        )

        # 3. Report By Product
        rec_prod = self.report_model.create({
            'report_type': 'report_by_product',
        })
        res_prod = self.report_model.purchase_report([rec_prod.id])
        lines_prod = [
            line for line in res_prod['report_lines']
            if line.get('default_code') in ('LAP_01', 'MOU_02')
        ]
        self.assertEqual(len(lines_prod), 2)
        prod_map = {line['default_code']: line for line in lines_prod}
        self.assertIn('LAP_01', prod_map)
        self.assertIn('MOU_02', prod_map)
        # LAP_01: 2 on PO1 (1800) + 5 on PO3 (4250) = 7 qty, 6050 total
        self.assertEqual(prod_map['LAP_01']['qty'], 7.0)
        self.assertEqual(prod_map['LAP_01']['amount_total'], 6050.0)
        # MOU_02: 10 on PO2 (300) + 5 on PO3 (140) = 15 qty, 440 total
        self.assertEqual(prod_map['MOU_02']['qty'], 15.0)
        self.assertEqual(prod_map['MOU_02']['amount_total'], 440.0)

        # 4. Report By Categories
        rec_cat = self.report_model.create({
            'report_type': 'report_by_categories',
        })
        res_cat = self.report_model.purchase_report([rec_cat.id])
        lines_cat = [
            line for line in res_cat['report_lines']
            if line.get('name') == self.category.display_name
        ]
        self.assertEqual(len(lines_cat), 1)
        self.assertEqual(lines_cat[0]['qty'], 22.0)
        self.assertEqual(lines_cat[0]['amount_total'], 6490.0)

        # 5. Report By Purchase Representative
        rec_rep = self.report_model.create({
            'report_type': 'report_by_purchase_representative',
        })
        res_rep = self.report_model.purchase_report([rec_rep.id])
        self.assertIsInstance(res_rep['report_lines'], list)
        self.assertTrue(len(res_rep['report_lines']) > 0)

        # 6. Report By State
        rec_state = self.report_model.create({
            'report_type': 'report_by_state',
        })
        res_state = self.report_model.purchase_report([rec_state.id])
        self.assertIsInstance(res_state['report_lines'], list)
        self.assertTrue(len(res_state['report_lines']) > 0)

    def test_purchase_report_with_date_filters(self):
        """Test purchase_report with date_from and date_to parameters."""
        now = fields.Datetime.now()
        date_from = now - timedelta(days=5)
        date_to = now + timedelta(days=1)

        record = self.report_model.create({
            'report_type': 'report_by_order',
            'date_from': date_from,
            'date_to': date_to,
        })
        res = self.report_model.purchase_report([record.id])
        self.assertTrue(len(res['report_lines']) >= 3)

        # Future date range returning no records
        future_record = self.report_model.create({
            'report_type': 'report_by_order',
            'date_from': now + timedelta(days=10),
            'date_to': now + timedelta(days=20),
        })
        future_res = self.report_model.purchase_report([future_record.id])
        self.assertEqual(len(future_res['report_lines']), 0)

    def test_get_report_values_post_processing(self):
        """Test post processing in _get_report_values."""
        # 1. Test product code and name permutations
        test_rows = [
            {
                'product': 'Widget A',
                'default_code': 'WA01',
                'note': '<p>Notice</p>',
            },
            {'product': 'Widget B', 'default_code': False},
            {'product': False, 'default_code': 'WA03'},
            {'product': False, 'default_code': False},
            {'categ_id': self.category.id, 'name': 'Old Name'},
            {'categ_id': 99999999, 'name': 'Fallback Name'},
            {'categ_id': False, 'name': 'Should Be Cleared'},
            {'name': {'en_US': 'English Name', 'fr_FR': 'Nom Francais'}},
            {'name': {'fr_FR': 'Seulement Francais'}},
            {'name': {}},
        ]
        mock_data = {
            'model': self.report_model,
            'report_type': 'report_by_order',
        }

        # Call _get_report_values with custom sub-lines to trigger all branches
        with patch.object(
            type(self.report_model),
            '_get_report_sub_lines',
            return_value=[test_rows]
        ):
            result = self.report_model._get_report_values(mock_data)
            processed_lines = result['PURCHASE']

            self.assertEqual(processed_lines[0]['product'], '[WA01] Widget A')
            self.assertEqual(processed_lines[0]['note'], 'Notice')
            self.assertEqual(processed_lines[1]['product'], 'Widget B')
            self.assertEqual(processed_lines[2]['product'], '[WA03]')
            self.assertEqual(processed_lines[3]['product'], '')
            self.assertEqual(
                processed_lines[4]['name'], self.category.display_name
            )
            self.assertEqual(processed_lines[5]['name'], 'Fallback Name')
            self.assertEqual(processed_lines[6]['name'], '')
            self.assertEqual(processed_lines[7]['name'], 'English Name')
            self.assertEqual(processed_lines[8]['name'], 'Seulement Francais')
            self.assertEqual(processed_lines[9]['name'], '')

        # 2. Test when report_res is a single dict (lines 390-403)
        dict_row = {
            'note': '<b>Important</b>',
            'name': {'en_US': 'Header Name'},
            'desc': {'es_ES': 'Descripcion'},
            'empty': {},
        }
        with patch.object(
            type(self.report_model),
            '_get_report_sub_lines',
            return_value=dict_row
        ):
            mock_data_dict = {'model': self.report_model, 'report_type': False}
            res_dict = self.report_model._get_report_values(mock_data_dict)
            self.assertEqual(res_dict['PURCHASE']['note'], 'Important')
            self.assertEqual(res_dict['PURCHASE']['name'], 'Header Name')
            self.assertEqual(res_dict['PURCHASE']['desc'], 'Descripcion')
            self.assertEqual(res_dict['PURCHASE']['empty'], '')

    def test_get_purchase_xlsx_report_all_types(self):
        """Test XLSX generation for all 6 report types."""
        xlsx_test_cases = [
            (
                'report_by_order',
                [{
                    'name': 'PO001',
                    'date_order': '2026-10-25 10:00:00',
                    'partner': 'Vendor A',
                    'salesman': 'Rep A',
                    'sum': 10.0,
                    'amount_total': 1500.0,
                }],
            ),
            (
                'report_by_order_detail',
                [{
                    'name': 'PO002',
                    'date_order': '2026-10-25 10:00:00',
                    'partner': 'Vendor B',
                    'salesman': 'Rep B',
                    'default_code': 'PROD_01',
                    'product': 'Product One',
                    'price_unit': 100.0,
                    'sum': 5.0,
                    'amount_total': 500.0,
                }],
            ),
            (
                'report_by_product',
                [{
                    'name': 'Hardware',
                    'default_code': 'HW_01',
                    'product': 'Keyboard',
                    'qty': 20.0,
                    'amount_total': 600.0,
                }],
            ),
            (
                'report_by_categories',
                [{
                    'name': 'Electronics',
                    'qty': 50.0,
                    'amount_total': 5000.0,
                }],
            ),
            (
                'report_by_purchase_representative',
                [{
                    'name': 'John Doe',
                    'order': 3,
                    'qty': 15.0,
                    'amount': 3200.0,
                }],
            ),
            (
                'report_by_state',
                [
                    {
                        'state': 'draft',
                        'order': 2,
                        'qty': 4.0,
                        'amount': 800.0,
                    },
                    {
                        'state': 'sent',
                        'order': 1,
                        'qty': 10.0,
                        'amount': 300.0,
                    },
                    {
                        'state': 'purchase',
                        'order': 5,
                        'qty': 25.0,
                        'amount': 12000.0,
                    },
                ],
            ),
        ]

        for report_type, sample_lines in xlsx_test_cases:
            # Case A: With Date Filters
            filters_with_date = {
                'report_type': report_type,
                'date_from': '2026-01-01 00:00:00',
                'date_to': '2026-12-31 23:59:59',
            }
            resp_with_date = MockResponse()
            self.report_model.get_purchase_xlsx_report(
                data=json.dumps(filters_with_date),
                response=resp_with_date,
                report_data=json.dumps(sample_lines),
                dfr_data={},
            )
            self.assertTrue(
                len(resp_with_date.stream.getvalue()) > 0,
                f"XLSX with date generation failed for {report_type}"
            )

            # Case B: Without Date Filters
            filters_no_date = {
                'report_type': report_type,
            }
            resp_no_date = MockResponse()
            self.report_model.get_purchase_xlsx_report(
                data=json.dumps(filters_no_date),
                response=resp_no_date,
                report_data=json.dumps(sample_lines),
                dfr_data={},
            )
            self.assertTrue(
                len(resp_no_date.stream.getvalue()) > 0,
                f"XLSX without date generation failed for {report_type}"
            )

    def test_purchase_order_qweb_report(self):
        """Test report.purchase_report_generator.purchase_order_report."""
        qweb_model = self.env[
            'report.purchase_report_generator.purchase_order_report'
        ]

        # 1. Without purchase_order_report context
        res_no_ctx = qweb_model._get_report_values(None, {})
        self.assertIsNone(res_no_ctx)

        # 2. With context and valid dates
        data_input = {
            'report_data': {
                'orders': {
                    'date_from': '2026-01-01 00:00:00',
                    'date_to': '2026-12-31 23:59:59',
                },
                'filters': {
                    'report_type': 'Report By Order',
                },
                'report_lines': [
                    {'name': 'PO001', 'amount_total': 100.0},
                ],
            }
        }
        res_with_ctx = qweb_model.with_context(
            purchase_order_report=True
        )._get_report_values(None, data=data_input)
        self.assertIsNotNone(res_with_ctx)
        self.assertEqual(
            res_with_ctx['Filters']['report_type'], 'Report By Order'
        )
        self.assertEqual(res_with_ctx['date_from'], '01/01/26')
        self.assertEqual(res_with_ctx['date_to'], '31/12/26')
        self.assertEqual(len(res_with_ctx['report_main_line_data']), 1)
        self.assertEqual(res_with_ctx['company'], self.env.company)

        # 3. With context and empty dates
        data_empty_dates = {
            'report_data': {
                'orders': {},
                'filters': {'report_type': 'Report By State'},
                'report_lines': [],
            }
        }
        res_empty_dates = qweb_model.with_context(
            purchase_order_report=True
        )._get_report_values(None, data=data_empty_dates)
        self.assertEqual(res_empty_dates['date_from'], '')
        self.assertEqual(res_empty_dates['date_to'], '')

    def test_access_rights_no_purchase_group(self):
        """Test that user without purchase rights gets AccessError."""
        no_purchase_user = self.env['res.users'].create({
            'name': 'No Purchase User',
            'login': 'nopurchase_usr',
            'email': 'nopurchase_usr@example.com',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        user_model = self.report_model.with_user(no_purchase_user)
        report_record = user_model.create({
            'report_type': 'report_by_order',
        })
        with self.assertRaises(AccessError):
            user_model.purchase_report([report_record.id])

        with self.assertRaises(AccessError):
            user_model._get_report_sub_lines({
                'report_type': 'report_by_order',
            })

        resp = MockResponse()
        with self.assertRaises(AccessError):
            user_model.get_purchase_xlsx_report(
                data=json.dumps({'report_type': 'report_by_order'}),
                response=resp,
                report_data='[]',
                dfr_data={},
            )

    def test_multi_company_isolation(self):
        """Test that orders from other companies are not included."""
        company_2 = self.env['res.company'].create({
            'name': 'Secondary Company Isolation Test',
        })
        partner_c2 = self.env['res.partner'].create({
            'name': 'Vendor Company 2',
            'company_id': company_2.id,
        })
        po_c2 = self.env['purchase.order'].create({
            'name': 'PO_COMP2_SECRET',
            'partner_id': partner_c2.id,
            'company_id': company_2.id,
            'date_order': fields.Datetime.now(),
            'order_line': [
                Command.create({
                    'product_id': self.product_1.id,
                    'name': self.product_1.name,
                    'product_qty': 5.0,
                    'price_unit': 100.0,
                    'date_planned': fields.Datetime.now(),
                }),
            ],
        })
        # Running report under main company should not include po_c2
        lines = self.report_model.with_context(
            allowed_company_ids=[self.env.company.id]
        )._get_report_sub_lines({'report_type': 'report_by_order'})[0]
        po_ids = [line['id'] for line in lines if 'id' in line]
        self.assertNotIn(po_c2.id, po_ids)

    def test_report_by_order_detail_price_subtotal(self):
        """Test that report_by_order_detail uses line price_subtotal."""
        now = fields.Datetime.now()
        multi_line_po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'date_order': now,
            'order_line': [
                Command.create({
                    'product_id': self.product_1.id,
                    'name': self.product_1.name,
                    'product_qty': 2.0,
                    'price_unit': 500.0,
                    'date_planned': now,
                }),
                Command.create({
                    'product_id': self.product_2.id,
                    'name': self.product_2.name,
                    'product_qty': 1.0,
                    'price_unit': 200.0,
                    'date_planned': now,
                }),
            ],
        })
        # Order total is 1200, line 1 subtotal is 1000, line 2 is 200
        res = self.report_model._get_report_sub_lines({
            'report_type': 'report_by_order_detail',
        })[0]
        po_lines = [r for r in res if r.get('id') == multi_line_po.id]
        self.assertEqual(len(po_lines), 2)
        subtotals = {r['price_subtotal'] for r in po_lines}
        self.assertEqual(subtotals, {1000.0, 200.0})

        # Test QWeb rendering for order detail
        report_data = {
            'report_data': {
                'orders': {},
                'filters': {'report_type': 'Report By Order Detail'},
                'report_lines': po_lines,
            }
        }
        qweb_values = self.env[
            'report.purchase_report_generator.purchase_order_report'
        ].with_context(
            purchase_order_report=True
        )._get_report_values(None, data=report_data)
        html = self.env['ir.qweb']._render(
            'purchase_report_generator.report_order_detail',
            qweb_values,
        )
        self.assertIn('Price Subtotal', str(html))
