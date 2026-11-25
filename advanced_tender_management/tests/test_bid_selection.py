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
class TestBidSelection(TenderManagementTestCommon):
    """Tests for final bid selection wizard."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender(tender_state='bid_selection')
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
        self.assertEqual(self.tender.tender_state, 'close')
        self.assertEqual(self.winning_bid.bidding_state, 'won')
        self.assertEqual(self.losing_bid.bidding_state, 'lost')
        self.assertEqual(len(self.tender.purchase_order_ids), 1)
        self.assertEqual(self.tender.purchase_order_ids.tender_id, self.tender)

    def test_action_confirm_purchase_requires_a_bid(self):
        self.wizard.tender_bid_id = False
        with self.assertRaises(UserError):
            self.wizard.action_confirm_purchase()
        self.assertFalse(self.tender.purchase_order_ids)
        self.assertEqual(self.tender.tender_state, 'bid_selection')

    def test_action_confirm_purchase_rejects_bid_of_other_tender(self):
        other_tender = self.create_tender(name='Other', tender_state='bid_selection')
        self.wizard.tender_bid_id = self.create_bid(other_tender, self.vendor_1, 'qualified')
        with self.assertRaises(UserError):
            self.wizard.action_confirm_purchase()
        self.assertFalse(self.tender.purchase_order_ids)
