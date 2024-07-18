# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class SubscriptionCustomerPortal(portal.CustomerPortal):
    """A class representing a subscription-based customer portal.
    This class extends the functionality of the base CustomerPortal class to
    provide features specific to subscription management and interactions."""

    def _prepare_home_portal_values(self, counters):
        """Values for /my & /my/home routes template rendering.
        Includes the record count for subscription order."""
        values = super()._prepare_home_portal_values(counters)
        if 'subscription_count' in counters:
            subscription_count = request.env[
                'subscription.package'].sudo().search_count(
                [('partner_id', '=', request.env.user.partner_id.id),
                 ('is_closed', '=', False)])
            values['subscription_count'] = subscription_count
        return values

    @http.route('/my/subscription_order',
                type='http', auth='user', website=True)
    def portal_my_subscription_orders(self, page=1, sortby=None, filterby=None,
                                      search=None, search_in='all',
                                      groupby='none'):
        """Values for /my/subscription_order routes template rendering."""
        values = self._prepare_portal_layout_values()
        subscription = request.env['subscription.package'].sudo()
        domain = [('partner_id', '=', request.env.user.partner_id.id),
                  ('is_closed', '=', False)]
        if not sortby:
            sortby = 'start_date'
        subscription_count = subscription.search_count(domain)
        pager = portal_pager(
            url="/my/subscription_order",
            url_args={'sortby': sortby, 'search_in': search_in,
                      'search': search, 'groupby': groupby},
            total=subscription_count, page=page, step=self._items_per_page)
        subscription_order = subscription.search(
            domain, limit=self._items_per_page, offset=pager['offset'])
        grouped_subscriptions = False
        values.update({
            'subscriptions': subscription_order,
            'grouped_subscriptions': grouped_subscriptions,
            'page_name': 'Subscription',
            'pager': pager,
            'default_url': '/my/subscription_order',
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'groupby': groupby,
            'filterby': filterby})
        return request.render(
            "website_subscription_package.portal_my_subscriptions", values)

    @http.route(
        ['/my/subscription_order/<int:subscription>',
         '/my/subscription_order/id=<int:subscription>/state=<string:state>'],
        type='http', auth="user", website=True)
    def subscription_page(self, subscription=None, state=None):
        """Render subscription page."""
        subscription = request.env['subscription.package'].sudo().browse(
            subscription)
        cancel_reason = request.env['subscription.package.stop'].sudo().search(
            [])
        users = request.env['res.users'].sudo().search([])
        if state == 'Draft':
            subscription.button_start_date()
        try:
            subscription.check_access_rights('read')
            subscription.check_access_rule('read')
        except AccessError:
            return request.website.render("website.403")
        return request.render(
            "website_subscription_package.subscription_page", {
                'subscription': subscription.sudo(),
                'users': users,
                'close_reasons': cancel_reason})

    @http.route(
        ['/my/subscription_order/cancel'],
        type='http', auth="user", website=True)
    def subscription_cancel(self, **post):
        """Render subscription page."""
        subscription = request.env['subscription.package'].sudo().browse(
            int(post.get('subscription_id')))
        subscription.is_closed = True
        subscription.close_reason_id = int(post.get('reason'))
        subscription.closed_by = int(post.get('user'))
        subscription.close_date = post.get('date_closed')
        stage = (request.env['subscription.package.stage'].search([
            ('category', '=', 'closed')]).id)
        values = {'stage_id': stage, 'is_to_renew': False}
        subscription.write(values)
        for lines in subscription.sale_order_id.order_line.filtered(
                lambda x: x.product_template_id.is_subscription == True):
            lines.qty_invoiced = lines.product_uom_qty
            lines.qty_to_invoice = 0
        return request.render(
            "website_subscription_package.subscription_page",
            {'subscription': subscription.sudo()})
