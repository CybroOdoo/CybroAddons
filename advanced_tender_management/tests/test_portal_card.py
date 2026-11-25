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
import hashlib
from unittest.mock import patch

from odoo import Command
from odoo.tests import tagged
from odoo.tools import BinaryBytes, file_open

from odoo.addons.advanced_tender_management.models import portal_entry

from .common import TenderManagementHttpCommon

CARD = 'advanced_tender_management.portal_tenders_client'
ICON = 'advanced_tender_management/static/src/img/tender.svg'


@tagged('post_install', '-at_install')
class TestPortalTendersCard(TenderManagementHttpCommon):
    """Tenders card of the portal home page: shown to vendors, and to any
    user with bids, with the number of bids."""

    @classmethod
    def _portal_user(cls, login, partner):
        return cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': partner.name, 'login': login, 'password': login,
            'partner_id': partner.id,
            'group_ids': [Command.set([cls.env.ref('base.group_portal').id])],
        })

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tender = cls.create_tender(tender_state='bid_submission')
        other_tender = cls.create_tender(name='Other Tender', tender_state='bid_submission')
        cls.vendor_with_bids = cls._portal_user('card_vendor_bids', cls.vendor_1)
        cls.create_bid(cls.tender, cls.vendor_1)
        cls.create_bid(other_tender, cls.vendor_1)
        cls.vendor_without_bids = cls._portal_user('card_vendor_new', cls.vendor_2)
        customer = cls.env['res.partner'].create({'name': 'Card Customer'})
        cls.customer = cls._portal_user('card_customer', customer)
        bidding_customer = cls.env['res.partner'].create({'name': 'Bidding Customer'})
        cls.bidding_customer = cls._portal_user('card_bidding_customer', bidding_customer)
        cls.create_bid(cls.tender, bidding_customer)

    def _visible_for(self, user):
        card = self.env.ref(CARD)
        entries = self.env['portal.entry'].with_user(user).search([])
        return card in entries._filter_visible_portal_cards()

    def _counter_for(self, user):
        self.authenticate(user.login, user.login)
        return self.make_jsonrpc_request(
            '/my/counters', {'counters': {'tender_bid_count': 'client_category'}},
        )['tender_bid_count']

    def test_card_shown_to_vendors_only_by_rule(self):
        self.assertTrue(self._visible_for(self.vendor_with_bids))
        self.assertTrue(self._visible_for(self.vendor_without_bids))
        self.assertFalse(self._visible_for(self.customer))

    def test_counter_is_the_exact_number_of_bids(self):
        self.assertEqual(self._counter_for(self.vendor_with_bids), 2)
        self.assertEqual(self._counter_for(self.vendor_without_bids), 0)
        self.assertEqual(self._counter_for(self.bidding_customer), 1)

    def test_counter_added_to_existing_card_only_when_missing(self):
        card = self.env.ref(CARD)
        card.placeholder_count = False
        self.env['portal.entry']._update_tenders_card()
        self.assertEqual(card.placeholder_count, 'tender_bid_count')
        card.placeholder_count = 'custom_count'
        self.env['portal.entry']._update_tenders_card()
        self.assertEqual(card.placeholder_count, 'custom_count')

    def test_old_icon_replaced_custom_icon_kept(self):
        card = self.env.ref(CARD)
        with file_open(ICON, 'rb') as icon_file:
            current_icon = icon_file.read()
        self.assertIn(b'#374874', current_icon, "the card icon uses the portal icon colours")
        self.assertEqual(card.image.content, current_icon)

        old_icon = BinaryBytes(b'<svg>old</svg>')
        with patch.object(portal_entry, 'OLD_TENDERS_CARD_ICON_SHA256',
                          hashlib.sha256(old_icon.content).hexdigest()):
            card.image = old_icon
            self.env['portal.entry']._update_tenders_card()
            self.assertEqual(card.image.content, current_icon)

            custom_icon = BinaryBytes(b'<svg>custom</svg>')
            card.image = custom_icon
            self.env['portal.entry']._update_tenders_card()
            self.assertEqual(card.image.content, custom_icon.content)

    def test_portal_home_in_browser(self):
        self.start_tour('/my', 'tender_ui_portal_card_count', login='card_vendor_bids')
        self.start_tour('/my', 'tender_ui_portal_card_no_count', login='card_vendor_new')
        self.start_tour('/my', 'tender_ui_portal_card_hidden', login='card_customer')
