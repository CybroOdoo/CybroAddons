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
from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class PortalRepair(CustomerPortal):
    """Portal pages for the customers' repair requests."""

    def _prepare_portal_counter_values(self, counter):
        """Return (model, domain, access) used to count the portal card."""
        if counter == 'repair_count':
            return 'machine.repair', self._get_repair_domain(), 'sudo'
        return super()._prepare_portal_counter_values(counter)

    def _repair_get_page_view_values(self, repair, access_token, **kwargs):
        """Prepare the values for the repair detail page."""
        values = {'page_name': 'repair', 'repair': repair}
        return self._get_page_view_values(repair, access_token, values,
                                          'my_repair_history', False, **kwargs)

    def _get_repair_domain(self):
        """Return the domain limiting repairs to the current customer."""
        return [('customer_id', '=', request.env.user.partner_id.id)]

    @http.route(['/my/repair', '/my/repair/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_repair(self, page=1, date_begin=None, date_end=None,
                         sort=None):
        """Render the list of the customer's repair requests."""
        values = self._prepare_portal_layout_values()
        machine_repair = request.env['machine.repair'].sudo()
        domain = self._get_repair_domain()
        searchbar_sorting = {
            'state': {'label': request.env._('Status'), 'repair': 'state'},
        }
        if not sort:
            sort = 'state'
        repair_count = machine_repair.search_count(domain)
        pager = portal_pager(url="/my/repair",
                             url_args={'date_begin': date_begin, 'date_end': date_end, 'sort': sort},
                             total=repair_count,
                             page=page,
                             step=self._items_per_page)
        repair = machine_repair.search(domain,
                                       limit=self._items_per_page,
                                       offset=pager['offset'])
        request.session['my_repair_history'] = repair.ids[:100]
        values.update({
            'date': date_begin,
            'machine_repair': repair_count,
            'repair': repair,
            'page_name': 'repair',
            'pager': pager,
            'default_url': '/my/repair',
            'searchbar_sorting': searchbar_sorting,
            'sort': sort,

        })
        return request.render(
            "base_machine_repair_management.portal_my_repair_request", values)

    @http.route(['/my/repair/<int:repair_id>'], type='http', auth="public",
                website=True)
    def portal_my_repair_detail(self, repair_id, access_token=None, **kw):
        """Render the detail page of a repair request."""
        try:
            repair_sudo = self._document_check_access('machine.repair', repair_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._repair_get_page_view_values(repair_sudo, access_token,**kw)
        return request.render("base_machine_repair_management.portal_repair_page", values)
