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
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers import portal

RATINGS = ('1', '2', '3', '4', '5')


def portal_tickets_domain():
    """Tickets of the current customer"""
    partner = request.env.user.partner_id
    return [('customer_id', 'child_of', [partner.commercial_partner_id.id])]


class TicketPortal(portal.CustomerPortal):
    """Helpdesk tickets of the customer portal"""

    def _prepare_portal_counter_values(self, counter):
        """Count the tickets of the customer in the portal home"""
        if counter == 'ticket_count':
            return 'ticket.helpdesk', self._get_tickets_domain(), 'read'
        return super()._prepare_portal_counter_values(counter)

    def _get_tickets_domain(self):
        """Tickets of the current customer"""
        return portal_tickets_domain()

    def _get_ticket_sudo(self, ticket_id, access_token=None):
        """Return the ticket if the customer may access it, sudoed"""
        return self._document_check_access('ticket.helpdesk', ticket_id,
                                           access_token=access_token)

    @http.route(['/my/tickets'], type='http', auth="user", website=True)
    def portal_my_tickets(self, **kwargs):
        """Tickets of the customer"""
        tickets = request.env['ticket.helpdesk'].sudo().search(
            self._get_tickets_domain())
        request.session['my_tickets_history'] = tickets.ids[:100]
        values = self._prepare_portal_layout_values()
        values.update({
            'default_url': "/my/tickets",
            'tickets': tickets,
            'page_name': 'ticket',
        })
        return request.render("odoo_website_helpdesk.portal_my_tickets",
                              values)

    @http.route(['/my/tickets/<int:ticket_id>'], type='http', auth="public",
                website=True)
    def portal_tickets_details(self, ticket_id, access_token=None, **kwargs):
        """Details of a ticket of the customer"""
        try:
            ticket_sudo = self._get_ticket_sudo(ticket_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._get_page_view_values(
            ticket_sudo, access_token, {
                'page_name': 'ticket',
                'ticket': True,
                'details': ticket_sudo,
            }, 'my_tickets_history', False)
        return request.render("odoo_website_helpdesk.portal_ticket_details",
                              values)

    @http.route(['/my/tickets/download/<int:ticket_id>'], type='http',
                auth='public', website=True)
    def ticket_download_portal(self, ticket_id, access_token=None, **kwargs):
        """PDF of a ticket of the customer"""
        try:
            ticket_sudo = self._get_ticket_sudo(ticket_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        return self._show_report(model=ticket_sudo, report_type='pdf',
                                 report_ref='odoo_website_helpdesk.report_ticket',
                                 download=True)

    @http.route(['/rating/<int:ticket_id>'], type='http', auth="public",
                website=True, sitemap=False)
    def rating(self, ticket_id, access_token=None, **kwargs):
        """Rating form of a ticket, opened from the closing email"""
        try:
            ticket_sudo = self._get_ticket_sudo(ticket_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        return request.render('odoo_website_helpdesk.rating_form', {
            'ticket': ticket_sudo,
            'access_token': access_token or '',
        })

    @http.route(['/rating/<int:ticket_id>/submit'], type='http',
                auth="public", website=True, methods=['POST'], sitemap=False)
    def rating_backend(self, ticket_id, access_token=None, rating=None,
                       message=None, **kwargs):
        """Save the rating and the review of the customer"""
        try:
            ticket_sudo = self._get_ticket_sudo(ticket_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if rating not in RATINGS:
            return request.redirect(
                f'/rating/{ticket_id}?access_token={access_token or ""}')
        ticket_sudo.write({
            'customer_rating': rating,
            'review': (message or '').strip(),
        })
        ticket_sudo.message_post(
            body=self.env._('Rated %(rating)s/5: %(review)s',
                            rating=rating, review=message or ''),
            author_id=request.env.user.partner_id.id,
            message_type='comment', subtype_xmlid='mail.mt_note')
        return request.render('odoo_website_helpdesk.rating_thanks')
