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
from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import TenderManagementTestCommon


@tagged('post_install', '-at_install')
class TestTenderBiddingProductLines(TenderManagementTestCommon):
    """Tests for bidding product line actions."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender(tender_type='product_wise_vendor',
                                         tender_state='bid_evaluation')
        self.bid_1 = self.create_bid(self.tender, self.vendor_1, 'qualified', {
            self.product_1.id: 10,
            self.product_2.id: 15,
        })
        self.bid_2 = self.create_bid(self.tender, self.vendor_2, 'qualified', {
            self.product_1.id: 12,
            self.product_2.id: 18,
        })
        self.line_1 = self.bid_1.tender_bid_products_ids.filtered(
            lambda line: line.product_id == self.product_1
        )
        self.line_2 = self.bid_2.tender_bid_products_ids.filtered(
            lambda line: line.product_id == self.product_1
        )

    def test_compute_product_total(self):
        self.assertEqual(self.line_1.product_total, self.line_1.product_qty * self.line_1.product_price)

    def test_action_confirm_bid_marks_other_lines_for_reselect(self):
        self.line_1.action_confirm_bid()

        self.assertTrue(self.line_1.bid_chosen)
        self.assertEqual(self.line_1.bid_status, 'selected')
        self.assertTrue(self.line_2.bid_chosen)
        self.assertEqual(self.line_2.bid_status, 're_select')

    def test_action_reselect_bid_switches_selected_line(self):
        self.line_1.action_confirm_bid()

        self.line_2.action_reselect_bid()

        self.assertEqual(self.line_2.bid_status, 'selected')
        self.assertEqual(self.line_1.bid_status, 're_select')

    def test_action_selected_bid_returns_none(self):
        self.assertIsNone(self.line_1.action_selected_bid())

    def test_decimal_quantity_total(self):
        self.line_1.tender_line_id.product_qty = 2.5
        self.assertEqual(self.line_1.product_qty, 2.5)
        self.assertEqual(self.line_1.product_total, 25.0)

    def test_product_line_quantity_must_be_positive(self):
        for line in (self.tender.tender_product_line_ids[:1], self.line_1):
            for quantity in (0, -1):
                with self.subTest(model=line._name, quantity=quantity), \
                        mute_logger('odoo.sql_db'), self.assertRaises((IntegrityError, ValidationError)), \
                        self.env.cr.savepoint():
                    line.product_qty = quantity
                    line.flush_recordset()

    def test_section_line_quantity_is_not_checked(self):
        section = self.env['tender.product.lines'].create({
            'name': 'Section', 'display_type': 'line_section',
            'tender_id': self.tender.id, 'product_qty': 0,
        })
        section.flush_recordset()
        self.assertEqual(section.product_qty, 0)
