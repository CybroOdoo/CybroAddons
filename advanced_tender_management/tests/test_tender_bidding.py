# -*- coding: utf-8 -*-
from unittest.mock import patch

from .common import TenderManagementTestCommon


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

    def test_action_methods_update_state_and_send_mail(self):
        bid = self.create_bid(self.tender, self.vendor_1)

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail') as send_mail:
            bid.action_qualify()
            self.assertEqual(bid.qualification_stage, 'qualified')
            bid.action_disqualify()
            self.assertEqual(bid.qualification_stage, 'disqualified')
            bid.edit_request = True
            bid.action_approve_edit_request()

        self.assertEqual(bid.bidding_state, 'bid')
        self.assertFalse(bid.edit_request)
        self.assertEqual(send_mail.call_count, 3)
