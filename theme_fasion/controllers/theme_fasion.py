# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import http


class ThemeFasion(http.Controller):
    """
    To get data of dynamic snippets
    """
    @http.route('/get_categories', auth='public', type='json',
                website=True)
    def get_categories(self):
        """
        Data of categories snippet
        """
        category_ids = http.request.env['website'].sudo().browse(
            http.request.website.id
        ).category_ids
        values = {
            'categories': category_ids
        }
        response = http.Response(
            template='theme_fasion.categories_snippet', qcontext=values)
        return response.render()

    @http.route('/get_smart_clothing', auth='public', type='json',
                website=True)
    def get_smart_clothing(self, **kw):
        """
        Data of smart clothing snippet
        """
        smart_clothing_ids = http.request.env['website'].sudo().browse(
            http.request.website.id
        ).smart_clothing_ids
        values = {}
        if smart_clothing_ids:
            values.update({
                "categories": smart_clothing_ids,
                "current_category": smart_clothing_ids[
                    kw.get('current_id') - 1] if
                kw.get('current_id') else smart_clothing_ids[0],
            })
        response = http.Response(
            template='theme_fasion.smart_clothing_snippet', qcontext=values)
        return response.render()

    @http.route('/get_insta_shopping', auth='public', type='json',
                website=True)
    def get_insta_shopping(self):
        """
        Data of insta shopping snippet
        """
        insta_shopping_ids = http.request.env['website'].sudo().browse(
            http.request.website.id
        ).insta_shopping_ids
        values = {}
        if insta_shopping_ids:
            values.update({
                "posts": insta_shopping_ids,
            })
        response = http.Response(
            template='theme_fasion.insta_shopping_snippet', qcontext=values)
        return response.render()
