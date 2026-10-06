# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo.http import request
from odoo.addons.website_blog.controllers.main import WebsiteBlog


class CustomBlogController(WebsiteBlog):
    @http.route([
        '/blog',
        '/blog/page/<int:page>',
        '''/blog/<model("blog.blog"):blog>''',
        '''/blog/<model("blog.blog"):blog>/page/<int:page>'''
    ], type='http', auth="public", website=True)
    def blog(self, blog=None, page=1, search=None, **kwargs):
        domain = [('website_published', '=', True)]
        if blog:
            domain.append(('blog_id', '=', blog.id))
        if search:
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append(('subtitle', 'ilike', search))
        blog_post = request.env['blog.post']
        total_posts = blog_post.search_count(domain)
        pager_url = '/blog/%s' % blog.id if blog else '/blog'
        pager_args = {'search': search} if search else {}
        pager = request.website.pager(
            url=pager_url,
            total=total_posts,
            page=page,
            step=12,
            url_args=pager_args,
        )
        posts = blog_post.search(
            domain,
            limit=12,
            offset=pager['offset'],
            order='post_date desc'
        )
        values = {
            'posts': posts,
            'pager': pager,
            'blog': blog,
            'search': search,
            'opt_blog_sidebar_show': True,
        }
        return request.render('website_blog.blog_post_short', values)

    @http.route([
        '/blog/<model("blog.post"):blog_post>',
        '''/blog/<model("blog.blog"):blog>/<model("blog.post"):blog_post>''',
        '''/blog/<model("blog.blog"):blog>/post/<model("blog.post"):blog_post>'''
    ], type='http', auth="public", website=True)
    def blog_post(self, blog_post, blog=None, **kwargs):
        values = {
            'blog_post': blog_post,
            'opt_blog_post_sidebar': True,
        }
        return request.render('website_blog.blog_post_complete', values)


class BlogPostSearchRedirect(http.Controller):
    @http.route('/product_info', auth='public', type='json')
    def blog_post_search_match(self, query=None):
        query = (query or '').strip()
        if not query:
            return {'url': '/blog'}
        return {'url': '/blog?search=%s' % query}
