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
from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalController(CustomerPortal):
    """Portal page listing the bids of the vendor, and the bid counter of
    the Tenders card on the portal home page."""

    @staticmethod
    def _tender_bid_domain():
        """Bids of the current user."""
        return [('vendor_id', '=', request.env.user.partner_id.id)]

    def _prepare_portal_counter_values(self, counter):
        """Count the bids of the current user for the Tenders card."""
        if counter == 'tender_bid_count':
            return 'tender.bidding', self._tender_bid_domain(), 'sudo'
        return super()._prepare_portal_counter_values(counter)

    @http.route()
    def counters(self, counters, **kwargs):
        """Odoo only checks whether a card has at least one record; the
        Tenders card shows the actual number of bids."""
        res = super().counters(counters, **kwargs)
        if res.get('tender_bid_count'):
            res['tender_bid_count'] = request.env['tender.bidding'].sudo().search_count(
                self._tender_bid_domain())
        return res

    @http.route('/my/tenders', type='http', auth="user", website=True)
    def portal_my_tenders(self, **_kwargs):
        """Render the bids submitted by the current user."""
        bid_records = request.env['tender.bidding'].sudo().search(self._tender_bid_domain())
        return request.render('advanced_tender_management.portal_my_tenders', {
            'bid_records': bid_records,
            'page_name': 'tenders',
        })
