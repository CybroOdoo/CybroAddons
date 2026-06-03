# -*- coding: utf-8 -*-
from .common import TenderManagementTestCommon


class TestTenderBiddingProductLines(TenderManagementTestCommon):
    """Tests for bidding product line actions."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender(tender_type='product_wise_vendor')
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
