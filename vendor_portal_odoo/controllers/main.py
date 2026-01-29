# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Noorjahan N A (<https://www.cybrosys.com>)
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
from collections import OrderedDict

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal


class RFQCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        """RFQ's in home portal"""
        user = request.env.user.partner_id
        values = super()._prepare_home_portal_values(counters)
        if 'my_rfq_count' in counters:
            values['my_rfq_count'] = request.env[
                'rfq.vendor'].search_count(
                [('vendor_ids', 'in', user.ids)]) if request.env[
                'rfq.vendor'].check_access_rights(
                'read', raise_exception=False) else 0
        return values

    def _rfq_get_page_view_values(self, vendor_rfq, access_token, **kwargs):
        """RFQ Page values"""
        values = {
            'page_name': 'vendor_rfq',
            'vendor_rfq': vendor_rfq,
        }
        return self._get_page_view_values(vendor_rfq, access_token, values,
                                          'my_rfq_history', False, **kwargs)

    @http.route(['/my/vendor_rfqs', '/my/vendor_rfqs/page/<int:page>'],
                type='http', auth="public", website=True)
    def portal_my_vendor_rfqs(self, page=1, date_begin=None,
                              date_end=None, sortby=None, filterby=None, **kw):
        """Portal vendor RFQ's"""
        values = self._prepare_portal_layout_values()
        user = request.env.user.partner_id
        VendorRFQ = request.env['rfq.vendor'].search([])
        domain = [
            ('vendor_ids', 'in', user.ids), ('state', 'not in', ['draft'])]
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin),
                       ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'),
                     'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'},
        }
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [
                ('state', 'in', ['draft', 'in_progress', 'pending',
                                 'done', 'cancel'])]},
            'Done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
            'In Progress': {'label': _('In Progress'),
                            'domain': [('state', '=', 'in_progress')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        rfq_unit_count = VendorRFQ.search_count(domain)
        pager = portal_pager(
            url="/my/vendor_rfqs",
            url_args={'date_begin': date_begin, 'date_end': date_end,
                      'sortby': sortby, 'filterby': filterby},
            total=rfq_unit_count,
            page=page,
            step=self._items_per_page
        )

        orders = VendorRFQ.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        values.update({
            'date': date_begin,
            'rfqs': orders,
            'page_name': 'vendor_rfq',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/vendor_rfqs',
        })
        return request.render(
            "vendor_portal_odoo.portal_my_rfq",
            values)

    @http.route(['/my/vendor_rfq/<int:rfq_id>'], type='http', auth="public",
                website=True)
    def portal_my_vendor_rfq(self, rfq_id, access_token=None, **kw):
        """displaying the RFQ details"""
        rfq_details = request.env['rfq.vendor'].browse(int(rfq_id))
        vendor_quote = rfq_details.vendor_quote_history_ids.filtered(
            lambda x: x.vendor_id.id == request.env.user.partner_id.id)
        quoted_price = vendor_quote.quoted_price
        values = self._rfq_get_page_view_values(rfq_details, access_token, **kw)
        values['quoted_price'] = quoted_price
        values['vendor_quote'] = vendor_quote
        return request.render(
            "vendor_portal_odoo.portal_my_vendor_rfq", values)

    @http.route(['/quote/details'], type='http', auth="public", website=True)
    def quote_details(self, **post):
        """Quote details"""
        request.env['rfq.vendor.quote_history'].sudo().create({
            'vendor_id': request.env.user.partner_id.id,
            'quoted_price': float(post.get('price')),
            'estimate_date': post.get('delivery_date'),
            'note': post.get('additional_note'),
            'quote_id': post.get('rfq_id'),
        })
        return request.redirect('/my/vendor_rfq/%s' % (post.get('rfq_id')))
