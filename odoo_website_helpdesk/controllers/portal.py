# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
from odoo.addons.portal.controllers import portal
from odoo.http import request


class TicketPortal(portal.CustomerPortal):
    """ Controller for handling customer portal related actions related to
    helpdesk tickets.
    """
    def _prepare_home_portal_values(self, counters):
        """Prepares a dictionary of values to be used in the home portal view
        and get their count."""
        values = super()._prepare_home_portal_values(counters)
        if 'ticket_count' in counters:
            ticket_count = request.env['help.ticket'].search_count(
                self._get_tickets_domain())
            values['ticket_count'] = ticket_count
        return values

    def _get_tickets_domain(self):
        """ Checking domain"""
        return [('customer_id', '=', request.env.user.partner_id.id)]

    @http.route(['/my/tickets'], type='http', auth="user", website=True)
    def portal_my_tickets(self):
        """Displays a list of tickets for the current user in the user's
        portal."""
        domain = self._get_tickets_domain()
        tickets = request.env['help.ticket'].search(domain)
        values = {
            'default_url': "/my/tickets",
            'tickets': tickets,
            'page_name': 'ticket',
        }
        return request.render("odoo_website_helpdesk.portal_my_tickets",
                              values)


class WebsiteHelpDeskForm(http.Controller):
    """ This controller handles the helpdesk ticket form and its submission."""

    @http.route(['/helpdesk_ticket'], type='http', auth="public", website=True,
                sitemap=True)
    def helpdesk_ticket(self):
        """Render the helpdesk ticket form."""
        return request.render('odoo_website_helpdesk.ticket_form')
