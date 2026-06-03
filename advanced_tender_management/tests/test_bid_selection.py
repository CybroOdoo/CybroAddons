# -*- coding: utf-8 -*-
from unittest.mock import patch

from .common import TenderManagementTestCommon


class TestBidSelection(TenderManagementTestCommon):
    """Tests for final bid selection wizard."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender()
        self.winning_bid = self.create_bid(self.tender, self.vendor_1, 'qualified', {
            self.product_1.id: 5,
            self.product_2.id: 5,
        })
        self.losing_bid = self.create_bid(self.tender, self.vendor_2, 'qualified')
        self.wizard = self.env['bid.selection'].create({
            'current_tender_id': self.tender.id,
            'tender_bid_id': self.winning_bid.id,
        })

    def test_action_confirm_purchase_creates_po_and_updates_bids(self):
        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail'):
            self.wizard.action_confirm_purchase()

        self.assertTrue(self.tender.purchase_confirmed)
        self.assertEqual(self.winning_bid.bidding_state, 'won')
        self.assertEqual(self.losing_bid.bidding_state, 'lost')
        self.assertEqual(len(self.tender.purchase_order_ids), 1)
        self.assertEqual(self.tender.purchase_order_ids.tender_id, self.tender)
