# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    @http.route('/get_main_product', auth="public", type='jsonrpc',
                website=True)
    def get_main_product(self):
        """Function returns the main products values to the
        product_section snippet"""
        main_products = request.env['product.template'].sudo().search_read(
            [('website_published', '=', True)],
            order='create_date asc', limit=8)
        return main_products


class WebsiteBlog(http.Controller):
    """Class WebsiteBlog with function get_blog_post to fetch
       main blog and return to corresponding template"""
    @http.route('/get_blog_post', auth="public", type='jsonrpc',
                website=True)
    def get_blog_post(self):
        """Function returns the value of latest blog to
        the snippet od template id latest_blog"""
        posts = request.env['blog.post'].sudo().search_read(
            [('website_published', '=', True),
             ('post_date', '<=', fields.Datetime.now())],
            order='published_date desc', limit=4)
        return posts


class WebsiteContactUs(http.Controller):
    """Class WebsiteContactUs to with defined route to render contact us
    thanks template when successful contact is created"""
    @http.route('/contactus-thank-you', type="http", website=True,
                auth='public')
    def create_contact_us(self, **kw):
        """this function related to the above controller renders the template
        contactus_thanks after successful submission of contact us form"""
        return request.render("website.contactus_thanks", {})
