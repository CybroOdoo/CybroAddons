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
"""Test cases for Portal Entry inherited model."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPortalEntry(TransactionCase):
    """Test suite for portal.entry extension."""

    def test_filter_visible_portal_cards_includes_franchise_requests(self):
        """Test that franchise requests card is included in visible portal cards."""
        franchise_entry = self.env.ref(
            'franchise_management.portal_franchise_requests',
            raise_if_not_found=False,
        )
        self.assertTrue(franchise_entry, "portal_franchise_requests record should exist")

        all_cards = self.env['portal.entry'].search([])
        visible_cards = all_cards._filter_visible_portal_cards()
        self.assertIn(
            franchise_entry,
            visible_cards,
            "Franchise Requests entry must be in visible portal cards",
        )

