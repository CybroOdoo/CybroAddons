from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class ShowPortal(CustomerPortal):
    """ Prepare values for the home portal and retrieve shows based on user permissions."""
    def _prepare_home_portal_values(self, counters):
        """
            Prepare values for the home portal and retrieve the count
            of shows available based on user permissions.
        """
        values = super()._prepare_home_portal_values(counters)
        if 'shows_count' in counters:
            shows_count = request.env['movie.registration'].search_count([])

            values['shows_count'] = shows_count
        return values

    @http.route('/my/shows', type='http', auth="user", website=True)
    def my_subscription(self, **kw):
        """
            Retrieve shows for the user based on permissions and render them on the portal.
        """
        user = request.env.user
        if user.has_group('base.group_system'):
            shows = request.env['movie.registration'].sudo().search([])
        else:
            shows = request.env['movie.registration'].sudo().search([('partner_id', '=', user.partner_id.id)])
        values = {
            'shows': shows,
        }
        return request.render('show_booking_management.portal_my_shows', values)
