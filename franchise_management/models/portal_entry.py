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
"""Portal entry model inherit"""
from odoo import models


class PortalEntry(models.Model):
    """Inherit portal.entry to include franchise requests card."""
    _inherit = 'portal.entry'

    def _filter_visible_portal_cards(self):
        visible_entries = super()._filter_visible_portal_cards()
        franchise_entry = self.env.ref(
            'franchise_management.portal_franchise_requests',
            raise_if_not_found=False,
        )
        if franchise_entry and franchise_entry in self:
            visible_entries |= franchise_entry
        return visible_entries

