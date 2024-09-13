# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<https://www.cybrosys.com>)
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
#############################################################################
"""Franchise dealer controller"""
from odoo import http
from odoo.http import request


class FranchiseDealer(http.Controller):
    """Franchise dealer controller."""

    @http.route(['/franchise_menu'], type='http', auth="public", website=True)
    def dealer_create(self):
        """Creating a dealer form  in website."""
        state_rec = request.env['res.country.state'].sudo().search([])
        country_rec = request.env['res.country'].sudo().search([])
        franchise_agreement_rec = request.env[
            'franchise.agreement'].sudo().search([])
        return http.request.render("franchise_management.tmpl_dealer_request",
                                   {
                                       'state_rec': state_rec,
                                       'country_rec': country_rec,
                                       'franchise_agreement_rec':
                                           franchise_agreement_rec,
                                   })

    @http.route(['/franchise_menu/form/submit'], type='http', auth="public",
                website=True)
    def franchise_form_submit(self, **post):
        """Website dealer form submit function."""
        order = request.env['franchise.dealer'].sudo().create({
            'dealer_name': post.get('franchisee_name'),
            'dealer_mobile': post.get('dealer_mobile') or '',
            'dealer_phone': post.get('dealer_phone') or '',
            'dealer_mail': post.get('franchisee_email') or '',
            'dealer_website': post.get('dealer_website') or '',
            'street': post.get('street') or '',
            'city': post.get('city') or '',
            'country_id': post.get('country_id'),
            'zip': post.get('zip') or '',
            'state_id': post.get('state_id'),
            'dealer_occupation': post.get('dealer_occupation') or '',
            'dealer_qualification': post.get('dealer_qualification') or '',
            'contract_type_id': post.get('contract_type_id'),
            'monthly_target_amount': post.get('monthly_target_amount'),
            'business_city': post.get('business_city'),
            'business_country': post.get('business_country'),
            'experience': post.get('experience') or '',
            'site_area': post.get('site_area') or '',
            'site_type': post.get('site_type') or '',
            'site_location': post.get('site_location'),
            'investment_from': post.get('investment_from'),
            'investment_to': post.get('investment_to'),
            'advertisement': post.get('advertisement')
        })
        vals = {'order': order}
        return request.render("franchise_management.website_success_page",
                              vals)
