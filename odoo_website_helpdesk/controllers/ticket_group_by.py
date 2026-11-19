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


class TicketGroupBy(http.Controller):
    """Group the tickets of the customer portal"""

    @http.route(['/ticketgroupby'], type='jsonrpc', auth="user", website=True)
    def ticket_group_by(self, search_value='0', **kwargs):
        """Tickets of the customer grouped by stage or by type"""
        tickets = request.env['ticket.helpdesk'].sudo().search(
            portal_tickets_domain())
        if search_value == '1':
            groups = [(stage.name, tickets.filtered(
                lambda ticket, stage=stage: ticket.stage_id == stage))
                for stage in tickets.stage_id.sorted()]
        elif search_value == '2':
            groups = [(ticket_type.name, tickets.filtered(
                lambda ticket, ticket_type=ticket_type:
                ticket.ticket_type_id == ticket_type))
                for ticket_type in tickets.ticket_type_id]
            no_type = tickets.filtered(lambda ticket: not ticket.ticket_type_id)
            if no_type:
                groups.append((self.env._('No Type'), no_type))
        else:
            groups = [('', tickets)] if tickets else []
        return request.env['ir.ui.view']._render_template(
            'odoo_website_helpdesk.ticket_group_by_table',
            {'groups': groups})
