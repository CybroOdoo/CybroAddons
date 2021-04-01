# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import http, _
from odoo.http import request


class DescribingAttribute(http.Controller):

    @http.route('/get_product', auth='public', type='json', website=True)
    def get_products(self, **kwargs):
        blast_configuration = request.env.ref('theme_blast.blast_configuration_data')
        product_id = blast_configuration.best_deal
        values = {'product_id': product_id}
        response = http.Response(template='theme_blast.best_deal_template', qcontext=values)
        return response.render()

    @http.route('/get_product_snippet', auth='public', type='json',
                website=True)
    def get_best_products(self, **kwargs):
        blast_configuration = request.env.ref(
            'theme_blast.blast_configuration_data')
        products = blast_configuration.best_products
        values = {'products': products}
        response = http.Response(
            template='theme_blast.best_product_carousel_snippet',
            qcontext=values)
        return response.render()

    @http.route('/get_testimonial', auth='public', type='json', website=True)
    def get_testimonial(self, **kwargs):
        partners = request.env['res.partner'].search([('is_publish', '=', 'True')])
        values = {'partners': partners}
        response = http.Response(template='theme_blast.testimonials_snippet', qcontext=values)
        return response.render()

    @http.route('/get_countdown', auth='public', type='json', website=True)
    def get_countdown(self, **kwargs):
        blast_configuration = request.env.ref('theme_blast.blast_configuration_data')
        end_date = blast_configuration.date_end
        return end_date
