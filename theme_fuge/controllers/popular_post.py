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
from odoo import http, fields
from odoo.http import request
from odoo.addons.website_blog.controllers.main import WebsiteBlog


class WebsiteBlogInherit(WebsiteBlog):
    """Class WebsiteBlogInherit with multiple routes to fetch blog related
     data using function blog and blog_post"""

    @http.route()
    def blog(self, blog=None, tag=None, page=1, search=None, **opt):
        """On user choosing blog filters in the website blogs this function
        returns the blog of count 3 on order published_date descending"""
        order = 'published_date desc'
        dom = fields.Domain([
            ('website_published', '=', True),
            ('post_date', '<=', fields.Datetime.now()),
        ]) & fields.Domain(request.website.website_domain())
        posts = request.env['blog.post'].search(dom, limit=3, order=order)
        res = super(WebsiteBlogInherit, self).blog(blog=blog, tag=tag, page=1,
                                                   search=search, **opt)
        res.qcontext.update({'posts_popular': posts})
        return res

    @http.route()
    def blog_post(self, blog, blog_post, tag_id=None, page=1,
                  enable_editor=None, **post):
        """This function returns the popular top 3 blogs to the
        corresponding template of order published_date descending"""
        order = 'published_date desc'
        dom = (
                fields.Domain([
                    ('website_published', '=', True),
                    ('post_date', '<=', fields.Datetime.now()),
                ])
                & fields.Domain(request.website.website_domain())
        )
        posts = request.env['blog.post'].search(dom, limit=3, order=order)
        res = super(WebsiteBlogInherit, self).blog_post(blog, blog_post,
                                                        tag_id=tag_id, page=1,
                                                        enable_editor=None,
                                                        **post)
        res.qcontext.update({'posts_popular': posts})
        return res
