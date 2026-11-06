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

from .portal import portal_tickets_domain


class TicketSearch(http.Controller):
    """Search the tickets of the customer portal"""

    @http.route(['/ticketsearch'], type='jsonrpc', auth="user", website=True)
    def ticket_search(self, search_value='', **kwargs):
        """Tickets of the customer matching the number or the subject"""
        domain = portal_tickets_domain()
        if search_value:
            domain += ['|', ('name', 'ilike', search_value),
                       ('subject', 'ilike', search_value)]
        tickets = request.env['ticket.helpdesk'].sudo().search(domain)
        return request.env['ir.ui.view']._render_template(
            'odoo_website_helpdesk.ticket_table', {'tickets': tickets})
