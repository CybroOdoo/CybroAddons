# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo import http
from odoo.http import request

class ThemeSolarion(http.Controller):

    @http.route(['/'], type='http', auth="public", website=True)
    def home(self, **kw):
        """ Return home template """
        return request.render('theme_solarion.page_index')

    @http.route('/about', type='http', auth="public", website=True)
    def about(self, **kw):
        """ Return about template """
        return request.render('theme_solarion.page_about')

    @http.route('/contactus', type='http', auth="public", website=True)
    def contact(self, **kw):
        """ Return contact template """
        return request.render('theme_solarion.page_contact')

    @http.route('/impact', type='http', auth="public", website=True)
    def impact(self, **kw):
        """ Return impact template """
        return request.render('theme_solarion.page_impact')

    @http.route('/solutions', type='http', auth="public", website=True)
    def solutions(self, **kw):
        """ Return solution template """
        return request.render('theme_solarion.page_solutions')

    @http.route('/theme_solarion/get_solutions_data', type='json', auth="public", website=True)
    def get_solutions_data(self, **kw):
        """ Return the solution snippet required data for template """
        products = request.env['solarion.product'].sudo().search([])
        product_list = []
        for prod in products:
            product_list.append({
                'id': prod.id,
                'name': prod.name,
                'efficiency': prod.efficiency or '',
                'lifespan': prod.lifespan or '',
                'warranty': prod.warranty or '',
                'description': prod.description or '',
                'has_image': bool(prod.image),
            })
        featured_product = product_list[0] if product_list else None
        other_products = product_list[1:] if len(product_list) > 1 else []
        return {
            'featured_product': featured_product,
            'other_products': other_products,
        }

    @http.route('/technology', type='http', auth="public", website=True)
    def technology(self, **kw):
        """ Return technology template """
        return request.render('theme_solarion.page_technology')

    @http.route('/solarion/contact/submit', type='http', auth="public", website=True, methods=['POST'])
    def contact_submit(self, **kw):
        """ process the contact submission """
        # Extract form data
        name = kw.get('contact_name')
        email = kw.get('email_from')
        phone = kw.get('phone')
        property_type = kw.get('property_type', '')
        solution = kw.get('solution_interest', '')
        description = kw.get('description', '')

        if not name or not email or not phone:
            return request.redirect('/contactus?error=missing_fields')

        # Create CRM lead
        lead_vals = {
            'name': f"Website Lead: {name}",
            'contact_name': name,
            'email_from': email,
            'phone': phone,
            'description': f"Property Type: {property_type}\nSolution Interest: {solution}\nMessage:\n{description}",
            'type': 'lead'
        }
        request.env['crm.lead'].sudo().create(lead_vals)
        return request.redirect('/contactus/thank-you')

    @http.route('/contactus/thank-you', type='http', auth="public", website=True)
    def contact_thank_you(self, **kw):
        """ Return the thank you template """
        return request.render('theme_solarion.page_thank_you')
