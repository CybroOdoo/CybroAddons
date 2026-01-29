"""Pet sittings"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
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
from datetime import date
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager, \
    get_records_pager


class PortalSittingsSchedules(CustomerPortal):
    """This class is used to gets the sitting portal values"""

    def _prepare_home_portal_values(self, counters):
        """Preparing portal values for sittings"""
        values = super()._prepare_home_portal_values(counters)
        if 'sittings_count' in counters:
            sittings_count = request.env[
                'sitting.schedule'].sudo().search_count(
                self._get_sittings_domain()) \
                if request.env['sitting.schedule'].check_access_rights('read',
                                          raise_exception=False) else 0
            values['sittings_count'] = sittings_count
        return values

    def _sittings_get_page_view_values(self, sittings, access_token, **kwargs):
        """This is used to view the sittings page"""
        values = {
            'page_name': 'sittings',
            'sittings': sittings,
        }
        return self._get_page_view_values(sittings, access_token, values,
                                          'my_sittings_history', False,
                                          **kwargs)

    def _get_sittings_domain(self):
        """Function for domain condition"""
        return [('end_date', '<=', date.today())]

    @http.route(['/my/sittings', '/my/sittings/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_sittings(self, page=1, date_begin=None, date_end=None,
                           sortby=None):
        """This is used to shown the sittings values"""
        values = self._prepare_portal_layout_values()
        sitting = request.env['sitting.schedule']
        domain = self._get_sittings_domain()
        searchbar_sortings = {
            'date': {'label': _('Date'), 'sittings': 'number desc'},
        }
        if not sortby:
            sortby = 'date'
        sittings_count = sitting.search_count(domain)
        pager = portal_pager(
            url="/my/sitting",
            url_args={'date_begin': date_begin, 'date_end': date_end,
                      'sortby': sortby},
            total=sittings_count,
            page=page,
            step=self._items_per_page
        )
        sittings = sitting.search(domain, limit=self._items_per_page,
                                  offset=pager['offset'])
        request.session['my_sittings_history'] = sittings.ids[:100]
        values.update({
            'date': date_begin,
            'sittings': sittings,
            'page_name': 'sittings',
            'pager': pager,
            'default_url': '/my/sittings',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("pet_shop_management.portal_my_sittings", values)
