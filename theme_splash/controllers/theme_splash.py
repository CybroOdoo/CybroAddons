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
from odoo import fields, http
from odoo.addons.website_blog.controllers.main import WebsiteBlog
from odoo.http import request
from odoo.osv import expression


class WebsiteBlogInherit(WebsiteBlog):
    """Overrides the blog() and blog_post() methods to add recent posts to
    their respective contexts.It also sets limits and orders for the posts
    displayed on the blog and blog post pages."""

    @http.route()
    def blog(self, blog=None, tag=None, search=None, **opt):
        """It fetches recent blog posts that are published on the website and
        updates the context of the blog page with the recent posts."""
        posts = request.env['blog.post'].search(expression.AND([
            [('website_published', '=', True),
             ('post_date', '<=', fields.Datetime.now())],
            request.website.website_domain()
        ]), limit=3, order='published_date desc')
        res = super(WebsiteBlogInherit, self).blog(blog=blog, tag=tag, page=1,
                                                   search=search, **opt)
        res.qcontext.update({'posts_recent': posts})
        return res

    @http.route()
    def blog_post(self, blog, blog_post, tag_id=None, **post):
        """It adds a context variable 'posts_recent', which contains a list of
        recent blog posts (limited to 3) to be displayed on the blog
        post page."""
        posts = request.env['blog.post'].search(expression.AND([
            [('website_published', '=', True),
             ('post_date', '<=', fields.Datetime.now())],
            request.website.website_domain()
        ]), limit=3, order='published_date desc')
        res = super(WebsiteBlogInherit, self).blog_post(blog, blog_post,
                                                        tag_id=tag_id, page=1,
                                                        enable_editor=None,
                                                        **post)
        res.qcontext.update({'posts_recent': posts})
        return res
