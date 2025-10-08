# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, \
    pager as portal_pager


class PortalAccount(CustomerPortal):
    """PortalAccount for subscription"""

    @http.route(['/my/subscription/invoice'], type='http', auth="user",
                website=True)
    def portal_my_subscription_order(self, page=1, date_begin=None,
                                     date_end=None, sortby=None, filterby=None):
        """Rendered response for the '
        vehicle_subscription.portal_my_invoices_subscription' template,
         containing the subscription invoices."""
        partner = request.env.user.partner_id
        values = self._prepare_my_invoices_values(page, date_begin, date_end,
                                                  sortby, filterby)
        pager = portal_pager(**values['pager'])
        domain = [
            ('invoice_line_ids.product_id', 'like', 'Vehicle Subscription'),
            ('partner_id', '=', partner.id)
        ]
        values.update({
            'invoices': request.env['account.move'].sudo().search(domain),
            'pager': pager,
        })
        return request.render(
            "vehicle_subscription.portal_my_invoices_subscription", values)

    def _prepare_home_portal_values(self, counters):
        """Prepare the values for the home portal page."""
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if 'subscription_count' in counters:
            values['subscription_count'] = request.env['account.move'].sudo() \
                .search_count(
                [(
                 'invoice_line_ids.product_id', 'like', 'Vehicle Subscription'),
                 ('partner_id', '=', partner.id)])
        return values
