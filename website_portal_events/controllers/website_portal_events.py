# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
from datetime import date, timedelta
from odoo import fields, http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.osv import expression
from odoo.osv.expression import OR, AND
from odoo.addons.portal.controllers.portal import CustomerPortal, \
    pager as portal_pager


class PortalEvent(CustomerPortal):
    """PortalEvent helps to show the information of all events in the
     customer portal"""

    def _prepare_home_portal_values(self, counters):
        """Which will set all portal values. And return total events count"""
        values = super()._prepare_home_portal_values(counters)
        if 'event_count' in counters:
            event_count = request.env['event.registration'].search_count(
                self._get_events_domain()) \
                if request.env['event.registration'].check_access_rights('read',
                                                                         raise_exception=False) else 0
            values['event_count'] = event_count
        return values

    def _get_events_domain(self):
        """Returns the events that are in stage 'cancel' and 'draft'"""
        return [('state', 'not in', ('cancel', 'draft'))]

    @http.route(['/my/events', '/my/events/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_events(self, page=1, date_begin=None, date_end=None,
                         sortby=None, filterby=None, search=None,
                         search_in='content', **kw):
        """Returns the corresponding event datas and pager information.
         Which will render a newtemplate to show the events"""
        values = self._prepare_my_event_values(page, date_begin, date_end,
                                               sortby, filterby,
                                               search, search_in)
        # Pager
        pager = portal_pager(**values['pager'])
        # Content according to pager and archive selected
        events = values['events'](pager['offset'])
        request.session['my_events_history'] = events.ids[:100]
        values.update({
            'events': events,
            'pager': pager,
        })
        return request.render("website_portal_events.portal_my_events", values)

    @http.route(['/my/event_data/<int:event>'],
                type='http', auth="public",
                website=True)
    def portal_my_helpdesk(self, event=None, access_token=None, **kw):
        """Helps to show the portal event datas. Which will redirected
         to the portal form"""
        try:
            event_sudo = self._document_check_access('event.registration',
                                                     event,
                                                     access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._get_event_page_view_values(event_sudo, access_token,
                                                  **kw)
        return request.render("website_portal_events.event_portal_form",
                              values)

    @http.route(['/download/event_data/<int:event>'],
                type='http', auth="public",
                website=True)
    def portal_my_event_download(self, event=None, access_token=None, **kw):
        """Helps to download event ticket from the portal"""
        if event:
            pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'event.action_report_event_registration_full_page_ticket',
                [event])
            pdfhttpheaders = [('Content-Type', 'application/pdf'),
                              ('Content-Length', str(len(pdf))),
                              ('Content-Disposition',
                               'attachment; filename=report.pdf')]
            response = request.make_response(pdf, headers=pdfhttpheaders)
            response.mimetype = 'application/pdf'
            return response
        else:
            return request.redirect('/my/event_data')

    def _get_event_page_view_values(self, event, access_token, **kwargs):
        """Get the page view values"""
        values = {
            'event': event,
            'page_name': 'event',
        }
        return self._get_page_view_values(event, access_token, values,
                                          'my_events_history', False, **kwargs)

    def _get_event_searchbar_sortings(self):
        """Sort the events based on the date and name"""
        return {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name asc'},
        }

    def _get_event_searchbar_filters(self):
        """Filter the events by All, Last month, This Month, Last Week,
         This Week, Last Year, This Year, Today and This Quarter"""
        # today = date.today()
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
                    ('create_date', '>=', this_week_start.strftime('%Y-%m-%d')),
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
                    ('create_date', '>=', this_year_start.strftime('%Y-%m-%d')),
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

    def _get_event_search_domain(self, search_in, search):
        """Returns the events for the given search(If we have not entered
         the full name which will also gives the output"""
        search_domain = []
        if search_in == 'all':
            search_domain.append([('name', 'ilike',
                                   f'{search}%')])
            search_domain.append([('email', 'ilike',
                                   f'{search}%')])
            search_domain.append([('phone', 'ilike',
                                   f'{search}%')])
        if search_in in ('event', 'all'):
            search_domain.append([('event_id', 'ilike',
                                   f'{search}%')])
        return OR(search_domain)

    def _get_event_searchbar_inputs(self):
        """Which will returns a dictionary of values by the search contents
         as Search in All, in Content, Search in Stages, Search in Event"""
        values = {
            'all': {'input': 'all', 'label': _('Search in All'), 'order': 1},
            'event': {'input': 'event', 'label': _('Search in Event'),
                      'order': 2},
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _prepare_my_event_values(self, page, date_begin, date_end, sortby,
                                 filterby, search, search_in,
                                 domain=None, url="/my/events"):
        """Add all event values to the portal. Which will return the
         values event, page, pager, filter, sort, and search"""
        values = self._prepare_portal_layout_values()
        Events = request.env['event.registration']
        domain = expression.AND([
            domain or [],
            self._get_events_domain(),
        ])
        searchbar_sortings = self._get_event_searchbar_sortings()
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        searchbar_filters = self._get_event_searchbar_filters()
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        searchbar_inputs = self._get_event_searchbar_inputs()
        if search and search_in:
            domain += self._get_event_search_domain(search_in, search)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin),
                       ('create_date', '<=', date_end)]
        values.update({
            'date': date_begin,
            # content according to pager and archive selected
            # lambda function to get the invoices recordset when the pager
            # will be defined in the main method of a route
            'events': lambda pager_offset: self._get_grouped_events(Events,
                                                                    domain,
                                                                    order,
                                                                    pager_offset),
            'page_name': 'event',
            'pager': {
                "url": url,
                "url_args": {'date_begin': date_begin, 'date_end': date_end,
                             'sortby': sortby, 'search_in': search_in,
                             'search': search},
                "total": Events.search_count(domain),
                "page": page,
                "step": self._items_per_page,
            },
            'default_url': url,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
        })
        return values

    def _get_grouped_events(self, Events, domain, order, pager_offset, ):
        """Returns the grouped evnts for a given domain"""
        events = Events.search(domain, order=order, limit=self._items_per_page,
                               offset=pager_offset)
        return events
