# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager, \
    get_records_pager


class PortalPets(CustomerPortal):
    """Getting portal values"""

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'pets_count' in counters:
            pets_count = request.env['product.product'].sudo().search_count(
                self._get_pets_domain()) \
                if request.env['product.product'].check_access_rights('read',
                                                                      raise_exception=False) else 0
            values['pets_count'] = pets_count
        return values

    def _pets_get_page_view_values(self, pets, access_token, **kwargs):
        """Page view values"""
        values = {
            'page_name': 'Pets Information',
            'pets': pets,
        }
        return self._get_page_view_values(pets, access_token, values,
                                          'my_pets_history', False, **kwargs)

    def _get_pets_domain(self):
        """Retrieving records based on the domain"""
        return [('is_pet', '=', True),
                ('responsible_id', '=', request.env.user.id)]

    @http.route(['/my/pets', '/my/pets/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_pets(self, page=1, date_begin=None, date_end=None,
                       sortby=None):
        """This is used to view the pets"""
        values = self._prepare_portal_layout_values()
        pet = request.env['product.product']
        domain = self._get_pets_domain()
        searchbar_sortings = {
            'date': {'label': _('Date'), 'pets': 'number desc'},
        }
        if not sortby:
            sortby = 'date'
        pets_count = pet.search_count(domain)
        pager = portal_pager(
            url="/my/pets",
            url_args={'date_begin': date_begin, 'date_end': date_end,
                      'sortby': sortby},
            total=pets_count,
            page=page,
            step=self._items_per_page
        )
        pets = pet.search(domain, limit=self._items_per_page,
                          offset=pager['offset'])
        request.session['my_pets_history'] = pets.ids[:100]
        values.update({
            'date': date_begin,
            'pets': pets,
            'page_name': 'pets',
            'pager': pager,
            'default_url': '/my/pets',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("pet_shop_management.portal_my_pets", values)

    @http.route(['/my/pets/<int:pets_id>'], type='http', auth="public",
                website=True)
    def portal_my_pets_detail(self, pets_id, access_token=None,
                              report_type=None, download=False, **kw):
        """Detail information of the pets"""
        try:
            pets_sudo = self._document_check_access('product.product', pets_id,
                                                    access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=pets_sudo,
                                     report_type=report_type,
                                     report_ref='pet_shop_management'
                                                '.view_product_product_form',
                                     download=download)
        values = self._pets_get_page_view_values(pets_sudo, access_token,
                                                 **kw)
        return request.render("pet_shop_management.portal_pets_page", values)
