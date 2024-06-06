# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2024-TODAY Cybrosys Techno Solutions
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request


class BestSnippet(http.Controller):
    """Class BestSnippet that inherits from http.Controller. """

    @http.route('/get_product', auth='public', type='json', website=True)
    def get_products(self):
        """Controller to reflect chosen product in 'Best Deal' snippet"""
        blast_configuration = request.env.ref(
            'theme_blast.blast_configuration_data')
        response = \
            http.Response(template='theme_blast.best_deal_template',
                          qcontext={
                              'product_id': blast_configuration.best_deal_id,
                          })
        return response.render()

    @http.route('/get_product_snippet', auth='public', type='json',
                website=True)
    def get_best_products(self):
        """Controller to reflect chosen products in 'Best Products Carousel'
         snippet"""
        blast_configuration = request.env.ref(
            'theme_blast.blast_configuration_data')
        response = http.Response(
            template='theme_blast.best_product_carousel_snippet',
            qcontext={'products': blast_configuration.best_products_ids})
        return response.render()

    @http.route('/get_asked_questions', auth='public', type='json',
                website=True)
    def get_asked_questions(self):
        """Controller to reflect asked questions in 'Asked questions'
         snippet"""
        blast_configuration = request.env.ref(
            'theme_blast.blast_configuration_data')
        response = http.Response(
            template='theme_blast.asked_questions_template',
            qcontext={
                'asked_questions': blast_configuration.asked_questions_ids})
        return response.render()

    @http.route('/get_testimonial', auth='public', type='json', website=True)
    def get_testimonial(self):
        """Controller to reflect partner feedback in 'Testimonial' snippet"""
        partners = request.env['res.partner'].search(
            [('is_published', '=', 'True')])
        response = http.Response(template='theme_blast.testimonials_snippet',
                                 qcontext={'partners': partners})
        return response.render()

    @http.route('/get_countdown', auth='public', type='json', website=True)
    def get_countdown(self):
        """Used to reflect sale end date in 'Best Deal' snippet"""
        blast_configuration = request.env.ref(
            'theme_blast.blast_configuration_data')
        return blast_configuration.date_end
