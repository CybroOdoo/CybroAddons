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

from odoo import api, models
from odoo.tools import BinaryBytes, file_open

TENDERS_CARD_XMLID = 'advanced_tender_management.portal_tenders_client'
TENDER_BID_COUNTER = 'tender_bid_count'
TENDERS_CARD_ICON = 'advanced_tender_management/static/src/img/tender.svg'
# SHA-256 of the first icon of the card, a light grey gavel that could hardly
# be seen on the card; it is replaced by the current icon on update.
OLD_TENDERS_CARD_ICON_SHA256 = (
    '7556a424c14f2df67171e730c4de73f3b2e2598e5fe8e168fd33092117c49ffb')


class PortalEntry(models.Model):
    """Show the Tenders card of the portal home page to vendors."""
    _inherit = 'portal.entry'

    def _filter_visible_portal_cards(self):
        """The Tenders card is shown to every vendor, even before their
        first bid. Other users see it once they have bids, through the
        bid counter of the card."""
        visible_entries = super()._filter_visible_portal_cards()
        tenders_card = self.env.ref(TENDERS_CARD_XMLID, raise_if_not_found=False)
        if tenders_card and tenders_card in self:
            partner = self.env.user.partner_id.sudo()
            if partner.is_vendor or partner.commercial_partner_id.is_vendor:
                visible_entries |= tenders_card
        return visible_entries

    @api.model
    def _update_tenders_card(self):
        """Bring the Tenders card of databases installed earlier up to date,
        as the card is not updated with the module: give it the bid counter
        and replace its first, hardly visible icon. A counter or an icon
        changed since is kept."""
        tenders_card = self.env.ref(TENDERS_CARD_XMLID, raise_if_not_found=False)
        if not tenders_card:
            return
        if not tenders_card.placeholder_count:
            tenders_card.placeholder_count = TENDER_BID_COUNTER
        icon = tenders_card.image.content if tenders_card.image else b''
        if hashlib.sha256(icon).hexdigest() == OLD_TENDERS_CARD_ICON_SHA256:
            with file_open(TENDERS_CARD_ICON, 'rb') as icon_file:
                tenders_card.image = BinaryBytes(icon_file.read())
