# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import http
from odoo.http import request


class HelpDeskTickets(http.Controller):
    """HelpDeskTickets controller handles the routes related to help tickets
     in the e-learning system."""
    @http.route(['/help/tickets'], type="json", auth="user")
    def elearning_snippet(self):
        """Retrieves help tickets from the database and renders the helpdesk
        dashboard template.
        :return: Rendered helpdesk dashboard template as a JSON response."""
        help_tickets = request.env['help.ticket'].sudo().search(
            [('stage_id.name', '=', 'Inbox')])
        tickets = [
            {'name': ticket.name, 'subject': ticket.subject, 'id': ticket.id}
            for ticket in
            help_tickets]
        response = http.Response(
            template='odoo_website_helpdesk_dashboard.dashboard_tickets',
            qcontext={'h_tickets': tickets})
        return response.render()
