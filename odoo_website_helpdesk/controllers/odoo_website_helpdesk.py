# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import CustomerPortal


class TicketPortal(portal.CustomerPortal):
    """It is a ticket portal for customer interactions. TicketPortal class
       provides functionality for managing tickets in a customer portal."""

    def _prepare_home_portal_values(self, counters):
        """Prepare the values for the home portal.
        Args:
            counters (dict): A dictionary containing counters for various
             elements.
        Returns:
            dict: A dictionary of values prepared for the home portal.
        """
        values = super()._prepare_home_portal_values(counters)
        if 'ticket_count' in counters:
            ticket_count = request.env['help.ticket'].search_count(
                self._get_tickets_domain())
            values['ticket_count'] = ticket_count
        return values

    def _get_tickets_domain(self):
        """
        Get the domain for retrieving tickets.
        Returns:
            list: A list representing the domain for retrieving tickets.
        """
        return [('customer_id', '=', request.env.user.partner_id.id)]

    @http.route(['/my/tickets'], type='http', auth="user", website=True)
    def portal_my_tickets(self):
        """Route for displaying the tickets in the customer portal. Which will
         return a HTTP response containing the rendered template"""
        domain = self._get_tickets_domain()
        tickets = request.env['help.ticket'].search(domain)
        return request.render("odoo_website_helpdesk.portal_my_tickets",
                              {
                                  'default_url': "/my/tickets",
                                  'tickets': tickets,
                                  'page_name': 'ticket',
                              })


class WebsiteHelpDesk(CustomerPortal):
    """WebsiteHelpDesk class provides functionality for managing helpdesk
     tickets in a website."""

    @http.route(['/helpdesk_ticket'], type='http', auth="public", website=True,
                sitemap=True)
    def helpdesk_ticket(self):
        """Which will display the ticket form in the website.
         Which will render a new template named ticket_form"""
        return request.render('odoo_website_helpdesk.ticket_form')

    @http.route(['/my/helpdesk/<int:ticket>', '/my/ticket/<int:ticket_id>'],
                type='http', auth="public",
                website=True)
    def portal_my_helpdesk(self, ticket=None, access_token=None, **kw):
        """Returns information about the ticket and access_token. And which
        will render a new template named helpdesk_portal_form"""
        try:
            ticket_sudo = self._document_check_access('help.ticket', ticket,
                                                      access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._ticket_get_page_view_values(ticket_sudo, access_token,
                                                   **kw)
        return request.render("odoo_website_helpdesk.helpdesk_portal_form",
                              values)

    def _ticket_get_page_view_values(self, ticket, access_token, **kwargs):
        """Get the page view values for the help desk ticket. Returns a
        dictionary of values containing ticket details and page name"""
        values = {
            'ticket': ticket,
            'page_name': 'ticket',
        }
        return self._get_page_view_values(ticket, access_token, values,
                                          'my_ticket_history', False, **kwargs)
