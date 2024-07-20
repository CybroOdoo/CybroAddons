# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http
from odoo.http import request


class HelpDeskTickets(http.Controller):
    @http.route(['/help/tickets'], type="json", auth="user")
    def elearning_snippet(self):
        tickets = []
        help_tickets = request.env['ticket.helpdesk'].sudo().search(
            [('stage_id.name', '=', 'Inbox')])
        for i in help_tickets:
            tickets.append(
                {'name': i.name, 'subject': i.subject, 'id': i.id})
        values = {
            'h_tickets': tickets
        }
        response = http.Response(
            template='odoo_website_helpdesk_dashboard.dashboard_tickets',
            qcontext=values)
        return response.render()
