# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (<https://www.cybrosys.com>)
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
from collections import OrderedDict
from odoo.osv import expression
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, \
    pager as portal_pager


class PortalAccount(CustomerPortal):
    """PortalAccount for subscription"""

    def _get_account_searchbar_sortings(self):
        """Website accounts search bar sorting options"""
        return {
            'date': {'label': _('Date'), 'order': 'invoice_date desc'},
            'duedate': {'label': _('Due Date'),
                        'order': 'invoice_date_due desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }

    def _get_account_searchbar_filters(self):
        """Function get the search bar filters"""
        return {
            'all': {'label': _('All'), 'domain': []},
            'invoices': {'label': _('Invoices'), 'domain': [
                ('move_type', 'in', ('out_invoice', 'out_refund'))]},
            'bills': {'label': _('Bills'), 'domain': [
                ('move_type', 'in', ('in_invoice', 'in_refund'))]},
        }

    def _prepare_my_invoices_values(self, page, date_begin, date_end, sortby,
                                    filterby, domain=None, url="/my/invoices"):
        """Function prepare the invoice value"""
        values = self._prepare_portal_layout_values()
        AccountInvoice = request.env['account.move']
        domain = expression.AND([
            domain or [],
            self._get_invoices_domain(),
        ])
        searchbar_sortings = self._get_account_searchbar_sortings()
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        searchbar_filters = self._get_account_searchbar_filters()
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin),
                       ('create_date', '<=', date_end)]
        values.update({
            'date': date_begin,
            'invoices': lambda pager_offset: AccountInvoice.search(
                domain,
                order=order,
                limit=self._items_per_page,
                offset=pager_offset),
            'page_name': 'invoice',
            'pager': {
                "url": url,
                "url_args": {'date_begin': date_begin, 'date_end': date_end,
                             'sortby': sortby},
                "total": AccountInvoice.search_count(domain),
                "page": page,
                "step": self._items_per_page,
            },
            'default_url': url,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return values

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
            ('partner_id', '=', partner.id), ('subscription_id', '!=', False)
        ]
        values.update({
            'invoices': request.env['account.move'].sudo().search(domain),
            'pager': pager,
            'page_name': 'subscription_home'
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
                    'invoice_line_ids.product_id', 'like',
                    'Vehicle Subscription'),
                    ('partner_id', '=', partner.id),
                    ('subscription_id', 'in',
                     request.env['fleet.subscription'].search([]).ids)])
        return values
