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
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http, fields
from odoo.http import request


class MainProduct(http.Controller):
    """Class MainProduct with function get_main_product to fetch
    main product and return to corresponding template"""
    @http.route('/get_main_product', auth="public", type='json',
                website=True)
    def get_main_product(self):
        """Function returns the main products values to the
        product_section snippet"""
        main_products = request.env['product.template'].sudo().search(
            [('website_published', '=', True)],
            order='create_date asc', limit=8)
        values = {
            'main_products': main_products,
        }
        response = http.Response(template='theme_fuge.product_snippet_section',
                                 qcontext=values)
        return response.render()


class WebsiteBlog(http.Controller):
    """Class WebsiteBlog with function get_blog_post to fetch
       main blog and return to corresponding template"""
    @http.route('/get_blog_post', auth="public", type='json',
                website=True)
    def get_blog_post(self):
        """Function returns the value of latest blog to
        the snippet od template id latest_blog"""
        posts = request.env['blog.post'].sudo().search(
            [('website_published', '=', True),
             ('post_date', '<=', fields.Datetime.now())],
            order='published_date desc', limit=4)
        values = {
            'posts_recent': posts,
        }
        response = http.Response(template='theme_fuge.latest_blog_section',
                                 qcontext=values)
        return response.render()


class WebsiteContactUs(http.Controller):
    """Class WebsiteContactUs to with defined route to render contact us
    thanks template when successful contact is created"""
    @http.route('/contactus-thank-you', type="http", website=True,
                auth='public')
    def create_contact_us(self, **kw):
        """this function related to the above controller renders the template
        contactus_thanks after successful submission of contact us form"""
        return request.render("website.contactus_thanks", {})


class WebsiteProductComparison(WebsiteSale):
    """Class WebsiteProductComparison with defined function to check
    the comparison settings is enabled in website config settings"""
    @http.route()
    def shop(self, **post):
        """Extracts the value of the module_website_sale_comparison field from
         the fetched configuration settings. This represents a boolean
         indicating whether product comparison is enabled or not"""
        res = super().shop(**post)
        res_config_settings = request.env['res.config.settings'].sudo().search(
            [], limit=1, order='id desc')
        boolean_product_comparison = (
            res_config_settings.module_website_sale_comparison)
        res.qcontext.update(
            {'boolean_product_comparison': boolean_product_comparison})
        return res
