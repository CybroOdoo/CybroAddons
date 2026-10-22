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
from odoo import models


class PortalEntry(models.Model):
    _inherit = 'portal.entry'

    def _filter_visible_portal_cards(self):
        visible_entries = super()._filter_visible_portal_cards()
        venue_entry = self.env.ref('venue_booking_management.portal_entry_venue_booking', raise_if_not_found=False)
        if venue_entry and venue_entry in self:
            visible_entries |= venue_entry
        return visible_entries
