# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import date
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class PortalSittingsSchedules(CustomerPortal):
    """ This class is used to get sitting portal values """

    def _prepare_portal_counter_values(self, counter):
        if counter == 'sittings_count':
            return 'sitting.schedule', self._get_sittings_domain(), 'read'
        return super()._prepare_portal_counter_values(counter)

    def _sittings_get_page_view_values(self, sittings, access_token, **kwargs):
        """ View sittings page values """
        values = {
            'page_name': 'sittings',
            'sittings': sittings,
        }
        return self._get_page_view_values(sittings, access_token, values,
                                          'my_sittings_history', False,
                                          **kwargs)

    def _get_sittings_domain(self):
        """ Function for sittings domain condition """
        domain = [('end_date', '>=', date.today())]
        user = request.env.user
        if not user.has_group('base.group_user'):
            domain += ['|', ('number_id.partner_id', '=', user.partner_id.id),
                       ('pet_info_ids.customer', '=', user.partner_id.id)]
        return domain

    @http.route(['/my/sittings', '/my/sittings/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_sittings(self, page=1, date_begin=None, date_end=None,
                           sortby=None):
        """ Display sittings in portal """
        values = self._prepare_portal_layout_values()
        sitting = request.env['sitting.schedule']
        domain = self._get_sittings_domain()
        searchbar_sortings = {
            'date': {
                'label': request.env._('Date'),
                'order': 'date_start desc, id desc',
            },
        }
        if not sortby or sortby not in searchbar_sortings:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        sittings_count = sitting.search_count(domain)
        pager = portal_pager(
            url="/my/sittings",
            url_args={'date_begin': date_begin, 'date_end': date_end,
                      'sortby': sortby},
            total=sittings_count,
            page=page,
            step=self._items_per_page
        )
        sittings = sitting.search(
            domain, order=order, limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_sittings_history'] = sittings.ids[:100]
        values.update({
            'date': date_begin,
            'sittings': sittings,
            'page_name': 'sittings',
            'pager': pager,
            'default_url': '/my/sittings',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'breadcrumbs_searchbar': True,
        })
        return request.render("pet_shop_management.portal_my_sittings", values)
