# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abbas P (odoo@cybrosys.com)
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
################################################################################
import base64
from collections import OrderedDict
from odoo.exceptions import AccessError, MissingError
from odoo import http
from odoo.http import request
from odoo.tools.image import image_process
from odoo.addons.portal.controllers.portal import CustomerPortal


class ReturnCustomerPortal(CustomerPortal):
    """Class for add portal for customer return"""

    def _prepare_portal_counter_values(self, counter):
        """Add the 'Return Orders' badge counter, scoped to the current partner"""
        if counter == 'return_count':
            partner = self.env.user.partner_id
            domain = [
                ('partner_id', 'child_of', [partner.commercial_partner_id.id]),
                ('state', 'in', ['draft', 'confirm', 'done', 'cancel']),
            ]
            return 'sale.return', domain, 'read'
        return super()._prepare_portal_counter_values(counter)

    @http.route(['/my/return_orders', '/my/return_orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_sale_return(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """Function for customer portal order return"""
        values = self._prepare_portal_layout_values()
        sale_return = request.env['sale.return']
        partner = request.env.user.partner_id
        domain = [('partner_id', 'child_of', [partner.commercial_partner_id.id])]

        searchbar_sortings = {
            'date': {'label': request.env._('Newest'), 'order': 'create_date desc'},
            'name': {'label': request.env._('Name'), 'order': 'name'},
            'sale': {'label': request.env._('Sale Order'), 'order': 'sale_order_id'},
        }

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_filters = {
            'all': {'label': request.env._('All'), 'domain': [('state', 'in', ['draft', 'confirm', 'done', 'cancel'])]},
            'confirm': {'label': request.env._('Confirmed'), 'domain': [('state', '=', 'confirm')]},
            'cancel': {'label': request.env._('Cancelled'), 'domain': [('state', '=', 'cancel')]},
            'done': {'label': request.env._('Done'), 'domain': [('state', '=', 'done')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        return_count = sale_return.search_count(domain)
        # pager
        pager = request.env.website.pager(
            url="/my/return_orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=return_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        orders = sale_return.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_return_history'] = orders.ids[:100]
        values.update({
            'date': date_begin,
            'orders': orders.sudo(),
            'page_name': 'Sale_Return',
            'default_url': '/my/return_orders',
            'pager': pager,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("website_return_management.portal_my_returns", values)

    @http.route(['/my/return_orders/<int:order_id>'], type='http', auth="user", website=True)
    def portal_my_return_detail(self, order_id=None, access_token=None, report_type=None, download=False, **kw):
        """Function for my order details"""
        try:
            order_sudo = self._document_check_access('sale.return', order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type,
                                     report_ref='website_return_management.report_sale_returns',
                                     download=download)

        values = self._sale_return_get_page_view_values(order_sudo, access_token, **kw)
        return request.render("website_return_management.portal_sale_return_page", values)

    def _sale_return_get_page_view_values(self, order, access_token, **kwargs):
        """Function for sale return get page view values"""
        def resize_to_48(b64source):
            if not b64source:
                b64source = request.env['ir.binary']._placeholder()
            else:
                b64source = base64.b64decode(b64source)
            return base64.b64encode(image_process(b64source, size=(48, 48)))
        values = {
            'orders': order,
            'resize_to_48': resize_to_48,
        }
        return self._get_page_view_values(order, access_token, values, 'my_return_history', False, **kwargs)
