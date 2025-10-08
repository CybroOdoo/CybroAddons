# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
import base64
from collections import OrderedDict
from geopy import Nominatim
import json
import pytz
from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, route
from odoo.tools import image_process
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import CustomerPortal


class ReturnCustomerPortal(CustomerPortal):
    """Passing values to the sale return templates"""

    def _prepare_home_portal_values(self, counters):
        """getting count of total sale returns"""
        values = super()._prepare_home_portal_values(counters)
        if 'return_count' in counters:
            values['return_count'] = request.env['sale.return'].search_count([
                ('state', 'in', ['draft', 'confirm', 'done', 'cancel'])])
        return values

    @http.route(['/my/return_orders', '/my/return_orders/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_sale_return(self, page=1, date_begin=None, date_end=None,
                              sortby=None, filterby=None):
        """Passing data to the /my/return_orders page"""
        values = self._prepare_portal_layout_values()
        sale_return = request.env['sale.return']
        domain = []
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
            'sale': {'label': _('Sale Order'), 'order': 'order_id'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin),
                       ('create_date', '<=', date_end)]
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [
                ('state', 'in', ['draft', 'confirm', 'done', 'cancel'])]},
            'confirm': {'label': _('Confirmed'),
                        'domain': [('state', '=', 'confirm')]},
            'cancel': {'label': _('Cancelled'),
                       'domain': [('state', '=', 'cancel')]},
            'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        # pager
        pager = request.website.pager(
            url="/my/return_orders",
            url_args={'date_begin': date_begin, 'date_end': date_end,
                      'sortby': sortby},
            total=sale_return.search_count(domain),
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        orders = sale_return.search(domain, order=order,
                                    limit=self._items_per_page,
                                    offset=pager['offset'])
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
        return request.render("all_in_one_website_kit.portal_my_returns",
                              values)

    @http.route(['/my/return_orders/<int:order_id>'], type='http',
                auth="public", website=True)
    def portal_my_return_detail(self, order_id=None, access_token=None,
                                report_type=None, download=False, **kw):
        """passing data to individual return orders"""
        try:
            order_sudo = self._document_check_access('sale.return', order_id,
                                                     access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(
                model=order_sudo, report_type=report_type,
                report_ref='all_in_one_website_kit.report_sale_returns',
                download=download)
        values = self._sale_return_get_page_view_values(order_sudo,
                                                        access_token, **kw)
        return request.render("all_in_one_website_kit.portal_sale_return_page",
                              values)

    def _sale_return_get_page_view_values(self, order, access_token, **kwargs):
        """ getting values to the function portal_my_return_detail"""
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
        return self._get_page_view_values(order, access_token, values,
                                          'my_return_history', False, **kwargs)

    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        """Replaces already existing work flow of portal view to redirect to
        new template with record values and count"""
        user = request.env.user.id
        partners = request.env.user
        group_id = request.env.ref('base.group_user')
        order_id = request.env['sale.order'].sudo()
        purchase_order = request.env['purchase.order'].sudo()
        account_move = request.env['account.move']
        project = request.env['project.project'].sudo()
        task = request.env['project.task'].sudo()
        config_parameters = request.env['ir.config_parameter'].sudo()
        number_project = ""
        projects_limited = ""
        tasks_limited = ""
        number_account = ""
        invoices_limited = ""
        show_project = request.env[
            'ir.config_parameter'
        ].sudo().get_param('portal_dashboard.is_show_project')
        show_account = request.env['ir.config_parameter'].sudo().get_param(
            'portal_dashboard.is_show_recent_invoice_bill')
        show_so_q = request.env[
            'ir.config_parameter'
        ].sudo().get_param('portal_dashboard.is_show_recent_so_q')
        show_po_rfq = request.env[
            'ir.config_parameter'
        ].sudo().get_param('portal_dashboard.is_show_recent_po_rfq')
        number_order = ""
        sale_orders_limited = ""
        quotations_limited = ""
        number_po = ""
        purchase_orders_limited = ""
        rfq_limited = ""
        if group_id in partners.groups_id:
            if show_so_q:
                number_order = request.env[
                    'ir.config_parameter'
                ].sudo().get_param('portal_dashboard.sale_count', 0)
                sale_orders_limited = order_id.search([
                    ('user_id', '=', user),
                    ('state', 'not in', ['draft', 'sent'])
                ], limit=int(number_order))
                quotations_limited = order_id.search([
                    ('user_id', '=', user),
                    ('state', 'in', ['sent'])
                ], limit=int(number_order))
            if show_po_rfq:
                number_po = config_parameters.get_param(
                    'portal_dashboard.purchase_count', 0)
                purchase_orders_limited = purchase_order.search([
                    ('user_id', '=', user),
                    ('state', 'not in', ['draft', 'sent', 'to approve'])
                ], limit=int(number_po))
                rfq_limited = purchase_order.search([
                    ('user_id', '=', user),
                    ('state', 'in', ['draft', 'sent', 'to approve'])
                ], limit=int(number_po))
            if show_project:
                number_project = config_parameters.get_param(
                    'portal_dashboard.project_count', 0)
                projects_limited = project.search([],
                                                  limit=int(number_project))
                tasks_limited = task.search([], limit=int(number_project))
            if show_account:
                number_account = config_parameters.get_param(
                    'portal_dashboard.account_count', 0)
                invoices_limited = account_move.search([
                    ('invoice_user_id', '=', user),
                    ('state', 'not in', ['draft', 'cancel'])
                ], limit=int(number_account))
            sale_orders = order_id.search([
                ('user_id', '=', user),
                ('access_token', '!=', False),
                ('state', 'not in', ['draft', 'sent'])
            ])
            quotations = order_id.search([
                ('user_id', '=', user),
                ('state', 'in', ['sent'])
            ])
            purchase_orders = purchase_order.search([
                ('user_id', '=', user),
                ('state', 'not in', ['draft', 'sent', 'to approve'])
            ])
            rfq = purchase_order.search([
                ('user_id', '=', user), ('state', 'in', ['sent', 'to approve'])
            ])
            projects = project.search([])
            tasks = task.search([])
            invoices = account_move.search([('access_token', '!=', False)])
        else:
            if show_so_q:
                number_order = config_parameters.get_param(
                    'portal_dashboard.sale_count', 0)
                sale_orders_limited = order_id.search([
                    ('partner_id', '=', partners.partner_id.id),
                    ('state', 'not in', ['draft', 'sent'])
                ], limit=int(number_order))
                quotations_limited = order_id.search([
                    ('partner_id', '=', partners.partner_id.id),
                    ('state', 'in', ['sent'])
                ], limit=int(number_order))
            if show_po_rfq:
                number_po = config_parameters.get_param(
                    'portal_dashboard.purchase_count', 0)
                purchase_orders_limited = purchase_order.search([
                    ('partner_id', '=', partners.partner_id.id),
                    ('state', 'not in', ['draft', 'sent', 'to approve'])
                ], limit=int(number_po))
                rfq_limited = purchase_order.search([
                    ('partner_id', '=', partners.partner_id.id),
                    ('state', 'in', ['draft', 'sent', 'to approve'])
                ], limit=int(number_po))
            if show_project:
                number_project = config_parameters.get_param(
                    'portal_dashboard.project_count', 0)
                projects_limited = project.search([('user_id', '=', user)],
                                                  limit=int(number_project))
                tasks_limited = task.search([('user_id', '=', user)],
                                            limit=int(number_project))
            if show_account:
                number_account = config_parameters.get_param(
                    'portal_dashboard.account_count', 0)
                invoices_limited = account_move.search([
                    ('partner_id', '=', partners.partner_id.id),
                    ('state', 'not in', ['draft', 'cancel'])
                ], limit=int(number_account))
            sale_orders = order_id.search([
                ('partner_id', '=', partners.partner_id.id),
                ('state', 'not in', ['draft', 'sent'])
            ])
            quotations = order_id.search([
                ('partner_id', '=', partners.partner_id.id),
                ('state', 'in', ['sent'])
            ])
            purchase_orders = purchase_order.search([
                ('partner_id', '=', partners.partner_id.id),
                ('state', 'not in', ['draft', 'sent', 'to approve'])
            ])
            rfq = purchase_order.search([
                ('partner_id', '=', partners.partner_id.id),
                ('state', 'in', ['sent', 'to approve'])
            ])
            projects = project.search([
                ('user_id', '=', user)
            ])
            tasks = task.search([('user_id', '=', user)])
            invoices = account_move.search([
                ('access_token', '!=', False)
            ])
        values = self._prepare_portal_layout_values()
        values['sale_order_portal'] = sale_orders
        values['quotation_portal'] = quotations
        values['purchase_orders_portal'] = purchase_orders
        values['rfq_portal'] = rfq
        values['projects_portal'] = projects
        values['tasks_portal'] = tasks
        values['invoices_portal'] = invoices
        values['number_so_portal'] = number_order
        values['number_po_portal'] = number_po
        values['number_account_portal'] = number_account
        values['number_project_portal'] = number_project
        values['sale_orders_limited'] = sale_orders_limited
        values['quotations_limited'] = quotations_limited
        values['purchase_orders_limited'] = purchase_orders_limited
        values['rfq_limited'] = rfq_limited
        values['invoices_limited'] = invoices_limited
        values['projects_limited'] = projects_limited
        values['tasks_limited'] = tasks_limited
        values['show_so_q'] = show_so_q
        values['show_po_rfq'] = show_po_rfq
        values['show_project'] = show_project
        values['show_account'] = show_account
        values['count_return_order'] = request.env['sale.return'].search_count(
            [('user_id', '=', request.env.uid)])
        return request.render(
            "all_in_one_website_kit.replace_dashboard_portal_view",
            values)

    @route()
    def account(self, **post):
        """ Super CustomerPortal class function and pass the api key value
        from settings using params to website view file"""

        res = super(ReturnCustomerPortal, self).account(**post)
        params = request.env['ir.config_parameter'].sudo()
        values = params.get_param('base_geolocalize.google_map_api_key')
        res.qcontext.update({
            'api': values
        })
        return res

    @http.route(['/geo/change/<coordinates>'], type='json', auth="none",
                website=False, csrf=False)
    def geo_changer(self, coordinates):
        """Controller function for get address details  from latitude and
        longitude that we pinpointed in map using geopy package from python

        Parameters ---------- coordinates :The stringify value from map that
        contains latitude and longitude

        Returns ------- Returning the address details back to view file from
        the converted Latitude and longitude
        """
        res = json.loads(coordinates)
        geolocator = Nominatim(user_agent="geoapiExercises")
        location = geolocator.reverse(
            str(res.get('lat')) + "," + str(res.get('lng')))
        city = "Undefined"
        suburb = "Undefined"
        state = "Undefined"
        country = "Undefined"
        p_code = "Undefined"
        if location:
            addresses = location.raw['address']
            if addresses.get('village'):
                city = addresses.get('village')
            if addresses.get('suburb'):
                suburb = addresses.get('suburb')
            state = addresses.get('state')
            country_code = addresses.get('country_code')
            country = pytz.country_names[country_code]
            if addresses.get('postcode'):
                p_code = addresses.get('postcode')
        return {
            'city': city,
            'suburb': suburb,
            'state': state,
            'country': country,
            'p_code': p_code,
        }

    @http.route(['/geo/location/<address>'], type='json', auth="none",
                website=False, csrf=False)
    def geo_location(self, address):
        """ Get value from city field in 'my_account' page and convert into
        lat and long and return back to website and set the map and fields
        Parameters ---------- address : The city name that in city field in
        website

        Returns
        -------
        Pass the value to website view and set required fields and map

        """
        locator = Nominatim(user_agent="myGeocoder")
        location = locator.geocode(address)
        geolocator = Nominatim(user_agent="geoapiExercises")
        location_country = geolocator.reverse(
            str(location.latitude) + "," + str(location.longitude))
        addresses = location_country.raw['address']
        country_code = addresses.get('country_code')
        country = pytz.country_names[country_code]
        p_code = "undefined"
        if addresses.get('postcode'):
            p_code = addresses.get('postcode')
        return {
            'lat': location.latitude,
            'lng': location.longitude,
            'country': country,
            'p_code': p_code
        }
