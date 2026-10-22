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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test cases for portal.entry extension."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPortalEntry(TransactionCase):
    """Test suite for portal.entry."""

    def test_filter_visible_portal_cards(self):
        """Test that venue booking portal entry is included in visible portal cards."""
        portal_entries = self.env['portal.entry'].search([])
        venue_entry = self.env.ref(
            'venue_booking_management.portal_entry_venue_booking', raise_if_not_found=False
        )
        if venue_entry:
            visible = portal_entries._filter_visible_portal_cards()
            self.assertIn(venue_entry, visible)
