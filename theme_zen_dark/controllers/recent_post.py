# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ASWIN A K(<https://www.cybrosys.com>)
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
from odoo.http import request
from odoo.osv import expression
from odoo.addons.website_blog.controllers.main import WebsiteBlog


class WebsiteBlogInherit(WebsiteBlog):
    """Class inherit Website Blog to check recent posts"""

    @http.route([
        '/blog',
        '/blog/page/<int:page>',
        '/blog/tag/<string:tag>',
        '/blog/tag/<string:tag>/page/<int:page>',
        '''/blog/<model("blog.blog"):blog>''',
        '''/blog/<model("blog.blog"):blog>/page/<int:page>''',
        '''/blog/<model("blog.blog"):blog>/tag/<string:tag>''',
        '''/blog/<model("blog.blog"):blog>/tag/<string:tag>/page/<int:page>''',
    ], type='http', auth="public", website=True, sitemap=True)
    def blog(self, blog=None, tag=None, page=1, search=None, **opt):
        """Function recent posted blog
           @returns: Dict of the blog sorted by recent dates
        """
        limit = 3
        order = 'published_date desc'
        dom = expression.AND([
            [('website_published', '=', True),
             ('post_date', '<=', fields.Datetime.now())],
            request.website.website_domain()
        ])
        posts = request.env['blog.post'].search(dom, limit=limit, order=order)
        res = super().blog(
            blog=blog, tag=tag, page=page, search=search, **opt)
        res.qcontext.update({'posts_recent': posts})
        return res

    @http.route([
        '''/blog/<model("blog.blog"):blog>/
        <model("blog.post","[('blog_id','=',blog.id)]"):blog_post>''',
    ], type='http', auth="public", website=True, sitemap=True)
    def blog_post(
            self, blog, blog_post, tag_id=None,
            page=1,enable_editor=None, **post):
        """Function recent posted blog posts
            @param blog_post: browse of the current post
            @param blog: browse of the current blog
            @param tag_id: current tag, if tag_id in parameters
            @param pager: a pager on the comments
            @returns Dictionary the blog posts sorted by recent dates
        """
        limit = 3
        order = 'published_date desc'
        dom = expression.AND([
            [('website_published', '=', True),
             ('post_date', '<=', fields.Datetime.now())],
            request.website.website_domain()
        ])
        posts = request.env['blog.post'].search(dom, limit=limit, order=order)
        res = super().blog_post(
            blog, blog_post, tag_id=tag_id, page=page,
            enable_editor=enable_editor, **post)
        res.qcontext.update({'posts_recent': posts})
        return res
