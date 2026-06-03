# -*- coding: utf-8 -*-
###############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.http import request


class PortalController(http.Controller):
    """Controller for managing portal-related actions."""

    @http.route('/my/tenders', type='http', auth="user", website=True)
    def portal_my_tenders(self, **_kwargs):
        """Renders the tenders associated with the current user."""
        current_partner_id = request.env.user.partner_id.id
        bid_records = request.env['tender.bidding'].sudo().search(
            [('vendor_id', '=', current_partner_id)])
        return request.render('advanced_tender_management.portal_my_tenders',
                              {'bid_records': bid_records})
