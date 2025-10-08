# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class TicketSearch(http.Controller):
    """Control for handle the  customer portal search
    filtering by the tickets."""
    @http.route(['/ticketsearch'], type='json', auth="public", website=True)
    def ticket_search(self, **kwargs):
        """ Display the list of tickets satisfying the searching condition.
        Searching the ticket  based on name or subject"""
        search_value = kwargs.get("search_value")
        tickets = request.env["help.ticket"].search(
            ['|', ('name', 'ilike', search_value),
             ('subject', 'ilike', search_value)])
        values = {
            'tickets': tickets,
        }
        response = http.Response(template='odoo_website_helpdesk.ticket_table',
                                 qcontext=values)
        return response.render()
