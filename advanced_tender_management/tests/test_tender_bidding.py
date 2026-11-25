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

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TenderManagementTestCommon


@tagged('post_install', '-at_install')
class TestTenderBidding(TenderManagementTestCommon):
    """Tests for tender bidding model behavior."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender()

    def test_create_sets_sequence_total_legit_and_rank(self):
        bid_1 = self.create_bid(self.tender, self.vendor_1, 'qualified', {
            self.product_1.id: 10,
            self.product_2.id: 20,
        })
        bid_2 = self.create_bid(self.tender, self.vendor_2, 'qualified', {
            self.product_1.id: 5,
            self.product_2.id: 10,
        })

        self.assertTrue(bid_1.name)
        self.assertEqual(bid_1.total_bidding_amount, 70)
        self.assertTrue(bid_1.legit_bid)
        self.assertEqual(bid_2.vendor_rank, 1)
        self.assertEqual(bid_1.vendor_rank, 2)

    def test_write_recomputes_vendor_rank(self):
        bid_1 = self.create_bid(self.tender, self.vendor_1, 'qualified')
        bid_2 = self.create_bid(self.tender, self.vendor_2, 'qualified', {
            self.product_1.id: 5,
            self.product_2.id: 5,
        })

        bid_1.write({'qualification_stage': 'disqualified'})

        self.assertEqual(bid_1.vendor_rank, 0)
        self.assertEqual(bid_2.vendor_rank, 1)

    def test_legit_bid_is_false_when_any_product_price_is_zero(self):
        bid = self.create_bid(self.tender, prices={
            self.product_1.id: 0,
            self.product_2.id: 20,
        })

        self.assertFalse(bid.legit_bid)

    def test_edit_request_approval_and_qualification(self):
        bid = self.create_bid(self.tender, self.vendor_1)
        bid.write({'bidding_state': 'bid_close', 'edit_request': True})

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail') as send_mail:
            with self.assertRaises(UserError):
                bid.action_approve_edit_request()
            self.tender.tender_state = 'bid_submission'
            bid.action_approve_edit_request()
            self.assertEqual(bid.bidding_state, 'bid')
            self.assertFalse(bid.edit_request)
            with self.assertRaises(UserError):
                bid.action_qualify()

            self.tender.action_bid_evaluation()
            self.assertEqual(bid.bidding_state, 'bid_close')
            bid.action_qualify()
            bid.action_qualify()
            self.assertEqual(bid.qualification_stage, 'qualified')
            bid.action_disqualify()
            self.assertEqual(bid.qualification_stage, 'disqualified')

        self.assertEqual(send_mail.call_count, 3)

    def test_bidding_close_clears_pending_edit_requests(self):
        self.tender.tender_state = 'bid_submission'
        requested = self.create_bid(self.tender, self.vendor_1)
        requested.write({'bidding_state': 'bid_close', 'edit_request': True})
        reopened = self.create_bid(self.tender, self.vendor_2)
        reopened.bidding_state = 'bid'

        self.tender.action_bid_evaluation()

        self.assertFalse(requested.edit_request)
        self.assertEqual(reopened.bidding_state, 'bid_close')

    def test_closing_or_cancelling_tender_loses_open_bids(self):
        self.tender.tender_state = 'bid_selection'
        bid = self.create_bid(self.tender, self.vendor_1, 'qualified')
        bid.bidding_state = 'bid_close'
        self.tender.action_close()
        self.assertEqual(bid.bidding_state, 'lost')
        with self.assertRaises(UserError):
            bid.action_qualify()

        other = self.create_tender(name='Cancelled', tender_state='bid_submission')
        other_bid = self.create_bid(other, self.vendor_2)
        other_bid.bidding_state = 'bid_close'
        other.action_cancel()
        self.assertEqual(other_bid.bidding_state, 'lost')

    def test_bid_lines_are_chosen_only_during_evaluation(self):
        bid = self.create_bid(self.tender, self.vendor_1)
        with self.assertRaises(UserError):
            bid.tender_bid_products_ids[:1].action_confirm_bid()
