# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Risvana AR (odoo@cybrosys.com)
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
from collections import OrderedDict
from datetime import timedelta
from odoo import fields,http, _
from odoo.http import request
from odoo.osv import expression
from odoo.osv.expression import OR
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class CustomerPortal(portal.CustomerPortal):
    """Class for Venue booking portal that gives the record and counts of the Bookings"""
    def _prepare_home_portal_values(self, counters):
        """ Function for finding the number of document """
        values = super()._prepare_home_portal_values(counters)
        uid = request.env.user.partner_id.id
        venue_booking_count = request.env['venue.booking'].search_count([('partner_id', '=', uid)])
        values.update({'venue_booking_count': venue_booking_count})
        return values

    @http.route(['/my/venue_booking', '/my/venue_booking/page/<int:page>'],
                type='http', auth='user',
                website=True)
    def create_venue_booking_management(self, page=1, date_begin=None,
                                        date_end=None,
                                        sortby=None, filterby=None,
                                        search=None,
                                        search_in='content', ):
        """ Function to fetch booking records and pass to the portal template"""
        uid = request.env.user.partner_id.id
        venue_booking_management = request.env['venue.booking'].sudo().search(
            [('partner_id', '=', uid)])
        values = self._prepare_my_booking_values(page, date_begin, date_end,
                                                 sortby, filterby, search,
                                                 search_in)
        # Pager
        pager = portal_pager(**values['pager'])
        venue = values['venue'](pager['offset'])
        request.session['my_venue_booking_history'] = venue.ids[:100]
        values.update({
            'venue_booking_management': venue_booking_management,
            'venues': venue,
            'pager': pager,
        })
        return request.render(
            "venue_booking_management.portal_my_venue_booking_documents",
            values)

    def _prepare_my_booking_values(self, page, date_begin, date_end, sortby,
                                   filterby, search, search_in,
                                   domain=None, url="/my/venue_booking"):
        """Add all event values to the portal. Which will return the
         values event, page, pager, filter, sort, and search"""
        values = self._prepare_portal_layout_values()
        Venue = request.env['venue.booking']
        domain = expression.AND([
            domain or [],
            self._get_booking_domain(),
        ])
        searchbar_sortings = self._get_venue_booking_searchbar_sortings()
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        searchbar_filters = self._get_venue_booking_searchbar_filters()
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        searchbar_inputs = self._get_venue_booking_searchbar_inputs()
        if search and search_in:
            domain += self._get_venue_booking_search_domain(search_in, search)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin),
                       ('create_date', '<=', date_end)]
        values.update({
            'date': date_begin,
            'venue': lambda pager_offset: self._get_grouped_venues(Venue,
                                                                   domain,
                                                                   order,
                                                                   pager_offset),
            'page_name': 'venue_booking',
            'pager': {
                "url": url,
                "url_args": {'date_begin': date_begin, 'date_end': date_end,
                             'sortby': sortby, 'search_in': search_in,
                             'search': search},
                "total": Venue.search_count(domain),
                "page": page,
                "step": self._items_per_page,
            },
            'default_url': url,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(
                sorted(searchbar_filters.items())),
            'filterby': filterby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
        })
        return values

    def _get_venue_page_view_values(self, venue, access_token, **kwargs):
        """Get the page view values"""
        values = {
            'venue': venue,
            'page_name': 'venue_booking',
        }
        return self._get_page_view_values(venue, access_token, values,
                                          'my_venue_booking_history', False, **kwargs)

    def _get_booking_domain(self):
        """Returns the booking that are in stage 'cancel' and 'draft'"""
        return [('state', 'not in', ('cancel', 'closed'))]

    def _get_venue_booking_searchbar_sortings(self):
        """Sort the booking based on the date and name"""
        return {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name asc'},
        }

    def _get_venue_booking_searchbar_filters(self):
        """Filter the events by All, Last month, This Month, Last Week,
         This Week, Last Year, This Year, Today and This Quarter"""
        today = fields.Date.today()
        this_month_start = today.replace(day=1)
        this_quarter_start = today.replace(day=1, month=((
                                                                     today.month - 1) // 3) * 3 + 1)
        this_week_start = today - timedelta(days=today.weekday())
        this_year_start = today.replace(month=1, day=1)
        return {
            'all': {'label': _('All'), 'domain': []},
            'last_month': {
                'label': _('Last Month'),
                'domain': [('create_date', '>=',
                            (this_month_start - timedelta(days=30)).strftime(
                                '%Y-%m-%d')),
                           ('create_date', '<=',
                            (this_month_start - timedelta(days=1)).strftime(
                                '%Y-%m-%d'))]
            },
            'this_month': {
                'label': _('This Month'),
                'domain': [
                    (
                        'create_date', '>=',
                        this_month_start.strftime('%Y-%m-%d')),
                    ('create_date', '<=', today.strftime('%Y-%m-%d'))]
            },
            'last_week': {
                'label': _('Last Week'),
                'domain': [('create_date', '>=',
                            (this_week_start - timedelta(days=7)).strftime(
                                '%Y-%m-%d')),
                           ('create_date', '<=',
                            (this_week_start - timedelta(days=1)).strftime(
                                '%Y-%m-%d'))]
            },
            'this_week': {
                'label': _('This Week'),
                'domain': [
                    (
                    'create_date', '>=', this_week_start.strftime('%Y-%m-%d')),
                    ('create_date', '<=', today.strftime('%Y-%m-%d'))]
            },
            'last_year': {
                'label': _('Last Year'),
                'domain': [('create_date', '>=',
                            (this_year_start - timedelta(days=365)).strftime(
                                '%Y-%m-%d')),
                           ('create_date', '<=',
                            (this_year_start - timedelta(days=1)).strftime(
                                '%Y-%m-%d'))]
            },
            'this_year': {
                'label': _('This Year'),
                'domain': [
                    (
                    'create_date', '>=', this_year_start.strftime('%Y-%m-%d')),
                    ('create_date', '<=', today.strftime('%Y-%m-%d'))]
            },
            'today': {
                'label': _('Today'),
                'domain': [('create_date', '=', today.strftime('%Y-%m-%d'))]
            },
            'this_quarter': {
                'label': _('This Quarter'),
                'domain': [
                    ('create_date', '>=',
                     this_quarter_start.strftime('%Y-%m-%d')),
                    ('create_date', '<=', today.strftime('%Y-%m-%d'))]
            }
        }

    def _get_venue_booking_search_domain(self, search_in, search):
        """Returns the events for the given search(If we have not entered
         the full name which will also gives the output"""
        search_domain = []
        if search_in == 'all':
            search_domain.append([('name', 'ilike',
                                   f'{search}%')])
            search_domain.append([('phone', 'ilike',
                                   f'{search}%')])
        if search_in in ('venue', 'all'):
            search_domain.append([('venue_id', 'ilike',
                                   f'{search}%')])
        return OR(search_domain)

    def _get_venue_booking_searchbar_inputs(self):
        """Which will returns a dictionary of values by the search contents
         as Search in All, in Content, Search in states, Search in Venues"""
        values = {
            'all': {'input': 'all', 'label': _('Search in All'), 'order': 1},
            'venue': {'input': 'venue', 'label': _('Search in Venue'),
                      'order': 2},
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _get_grouped_venues(self, Venue, domain, order, pager_offset, ):
        """Returns the grouped venues for a given domain"""
        venues = Venue.search(domain, order=order, limit=self._items_per_page,
                              offset=pager_offset)
        return venues

    @http.route(['/my/booking_data/<int:record>'], type='http',
                auth="user", website=True)
    def portal_my_venue_booking(self, record):
        """ Function to fetch data of selected visitors record and pass to
        the portal template"""
        booking_record = request.env['venue.booking'].sudo().browse(record)

        return http.request.render(
            'venue_booking_management.booking_portal_form',
            {'booking_record': booking_record,
             'page_name': 'venue_booking_management_record'})
