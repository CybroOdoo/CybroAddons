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
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class PortalPets(CustomerPortal):
    """ Getting pets portal values """

    def _prepare_portal_counter_values(self, counter):
        if counter == 'pets_count':
            return 'product.product', self._get_pets_domain(), 'read'
        return super()._prepare_portal_counter_values(counter)

    def _pets_get_page_view_values(self, pets, access_token, **kwargs):
        """ Page view values for pet details """
        values = {
            'page_name': 'pets',
            'pets': pets,
            'pet': pets,
        }
        return self._get_page_view_values(pets, access_token, values,
                                          'my_pets_history', False, **kwargs)

    def _get_pets_domain(self):
        """ Retrieving pet records based on user domain """
        user = request.env.user
        domain = [('is_pet', '=', True)]
        if not user.has_group('base.group_user'):
            domain += ['|', ('customer_id', '=', user.partner_id.id),
                       ('partner_id', '=', user.partner_id.id)]
        else:
            domain += ['|', '|', ('customer_id', '=', user.partner_id.id),
                       ('partner_id', '=', user.partner_id.id),
                       ('responsible_id', '=', user.id)]
        return domain

    @http.route(['/my/pets', '/my/pets/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_pets(self, page=1, date_begin=None, date_end=None,
                       sortby=None):
        """ View list of pets in portal """
        values = self._prepare_portal_layout_values()
        pet = request.env['product.product']
        domain = self._get_pets_domain()
        searchbar_sortings = {
            'date': {
                'label': request.env._('Date'),
                'order': 'create_date desc, id desc',
            },
            'name': {
                'label': request.env._('Name'),
                'order': 'name asc, id desc',
            },
        }
        if not sortby or sortby not in searchbar_sortings:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        pets_count = pet.search_count(domain)
        pager = portal_pager(
            url="/my/pets",
            url_args={'date_begin': date_begin, 'date_end': date_end,
                      'sortby': sortby},
            total=pets_count,
            page=page,
            step=self._items_per_page
        )
        pets = pet.search(domain, order=order, limit=self._items_per_page,
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
            'breadcrumbs_searchbar': True,
        })
        return request.render("pet_shop_management.portal_my_pets", values)

    @http.route(['/my/pets/<int:pets_id>'], type='http', auth="user",
                website=True)
    def portal_my_pets_detail(self, pets_id, access_token=None,
                              report_type=None, download=False, **kw):
        """ Detail information of pet """
        pet_record = request.env['product.product'].browse(pets_id)
        if not pet_record.exists() or not pet_record.is_pet:
            return request.redirect('/my')

        user = request.env.user
        if not user.has_group('base.group_user') and access_token is None:
            if (pet_record.customer_id != user.partner_id and
                    pet_record.partner_id != user.partner_id):
                return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=pet_record,
                                     report_type=report_type,
                                     report_ref='pet_shop_management.action_pet_report',
                                     download=download)
        values = self._pets_get_page_view_values(pet_record, access_token,
                                                 **kw)
        return request.render("pet_shop_management.portal_pets_page", values)
