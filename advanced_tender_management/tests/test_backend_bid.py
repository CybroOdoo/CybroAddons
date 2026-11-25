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
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from .common import TenderManagementTestCommon

SEND_MAIL = 'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'


@tagged('post_install', '-at_install')
class TestBackendBid(TenderManagementTestCommon):
    """Bids entered in the backend: lines taken from the tender, quantities
    locked to the tender and submission with the Submit Bid button."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender(tender_state='bid_submission')

    def _product_lines(self, bid):
        return bid.tender_bid_products_ids.filtered(lambda line: not line.display_type)

    def test_form_fills_lines_from_tender(self):
        with Form(self.env['tender.bidding']) as bid_form:
            bid_form.vendor_id = self.vendor_1
            bid_form.tender_id = self.tender
            for index, price in enumerate((10, 20)):
                with bid_form.tender_bid_products_ids.edit(index) as line:
                    line.product_price = price
        bid = bid_form.record
        lines = self._product_lines(bid)
        self.assertEqual(lines.tender_line_id, self.tender.tender_product_line_ids)
        self.assertEqual(lines.mapped('product_qty'), [3, 2])
        self.assertEqual(bid.total_bidding_amount, 10 * 3 + 20 * 2)
        self.assertEqual(bid.bidding_state, 'pre_qualification')

    def test_create_without_lines_takes_tender_lines(self):
        bid = self.env['tender.bidding'].create({
            'vendor_id': self.vendor_1.id, 'tender_id': self.tender.id})
        self.assertEqual(self._product_lines(bid).tender_line_id,
                         self.tender.tender_product_line_ids)

    def test_bid_line_quantity_cannot_differ_from_tender(self):
        bid = self.create_bid(self.tender, self.vendor_1)
        with self.assertRaises(ValidationError):
            self._product_lines(bid)[:1].product_qty = 7

    def test_tender_quantity_change_reaches_open_bids_only(self):
        open_bid = self.create_bid(self.tender, self.vendor_1)
        won_bid = self.create_bid(self.tender, self.vendor_2)
        won_bid.bidding_state = 'won'
        tender_line = self.tender.tender_product_line_ids[:1]
        tender_line.product_qty = 4.5
        self.assertEqual(self._product_lines(open_bid)[:1].product_qty, 4.5)
        self.assertEqual(self._product_lines(won_bid)[:1].product_qty, 3)

    def test_changing_tender_rebuilds_lines(self):
        other = self.create_tender(name='Other', tender_product_line_ids=[(0, 0, {
            'name': 'Only line', 'product_id': self.product_2.id, 'product_qty': 9})])
        bid = self.create_bid(self.tender, self.vendor_1)
        bid.tender_id = other
        self.assertEqual(self._product_lines(bid).tender_line_id,
                         other.tender_product_line_ids)
        self.assertEqual(self._product_lines(bid).product_qty, 9)

    def test_changing_tender_of_submitted_bid_is_refused(self):
        bid = self.create_bid(self.tender, self.vendor_1)
        bid.bidding_state = 'bid_close'
        with self.assertRaises(UserError):
            bid.tender_id = self.create_tender(name='Other')

    def test_submit_bid(self):
        bid = self.create_bid(self.tender, self.vendor_1)
        with patch(SEND_MAIL) as send_mail:
            bid.action_submit_bid()
        self.assertEqual(bid.bidding_state, 'bid_close')
        self.assertTrue(bid.bidding_date)
        self.assertIn(self.vendor_1, self.tender.registered_vendors_ids)
        send_mail.assert_called_once()
        self.assertTrue(bid._can_request_edit())

    def test_submit_bid_refused_outside_bid_submission(self):
        self.tender.tender_state = 'confirm'
        bid = self.create_bid(self.tender, self.vendor_1)
        with self.assertRaises(UserError):
            bid.action_submit_bid()
        self.assertEqual(bid.bidding_state, 'pre_qualification')

    def test_submit_bid_refused_when_already_submitted(self):
        bid = self.create_bid(self.tender, self.vendor_1)
        with patch(SEND_MAIL):
            bid.action_submit_bid()
            with self.assertRaises(UserError):
                bid.action_submit_bid()

    def test_submit_bid_refused_for_second_bid_of_vendor(self):
        self.create_bid(self.tender, self.vendor_1)
        second = self.create_bid(self.tender, self.vendor_1)
        with self.assertRaises(UserError):
            second.action_submit_bid()
