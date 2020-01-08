# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

import json

from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_blog.controllers.main import WebsiteBlog

from odoo import http, fields, SUPERUSER_ID
from odoo.http import request


class BlogInherit(WebsiteBlog):
    """Override class WebsiteBlog"""
    @http.route(['/blog',
                 '''/blog/<model("blog.blog", "[('website_id', 'in', (False, current_website_id))]"):blog>''',
                 '''/blog/<model("blog.blog"):blog>/page/<int:page>''',
                 '''/blog/<model("blog.blog"):blog>/tag/<string:tag>''',
                 '''/blog/<model("blog.blog"):blog>/tag/<string:tag>/page/<int:page>''',
                 '''/blog/search_content''',
                 ], type='http', auth="public", website=True, csrf=False)
    def blog(self, blog=None, tag=None, page=1, **opt):
        """function related to blog display"""
        date_begin, date_end, state = opt.get('date_begin'), opt.get('date_end'), opt.get('state')
        published_count, unpublished_count = 0, 0

        domain = request.website.website_domain()
        blog_post = request.env['blog.post']
        blogs = request.env['blog.blog'].search(domain, order="create_date asc", limit=2)
        # retrocompatibility to accept tag as slug
        active_tag_ids = tag and [int(unslug(t)[1]) for t in tag.split(',')] if tag else []
        if active_tag_ids:
            fixed_tag_slug = ",".join(slug(t) for t in request.env['blog.tag'].browse(active_tag_ids))
            if fixed_tag_slug != tag:
                return request.redirect(
                    request.httprequest.full_path.replace("/tag/%s/" % tag, "/tag/%s/" % fixed_tag_slug, 1), 301)
            domain += [('tag_ids', 'in', active_tag_ids)]
        if blog:
            domain += [('blog_id', '=', blog.id)]
        if date_begin and date_end:
            domain += [("post_date", ">=", date_begin), ("post_date", "<=", date_end)]

        if request.env.user.has_group('website.group_website_designer'):
            count_domain = domain + [("website_published", "=", True), ("post_date", "<=", fields.Datetime.now())]
            published_count = blog_post.search_count(count_domain)
            unpublished_count = blog_post.search_count(domain) - published_count

            if state == "published":
                domain += [("website_published", "=", True), ("post_date", "<=", fields.Datetime.now())]
            elif state == "unpublished":
                domain += ['|', ("website_published", "=", False), ("post_date", ">", fields.Datetime.now())]
        else:
            domain += [("post_date", "<=", fields.Datetime.now())]

        blog_url = QueryURL('', ['blog', 'tag'], blog=blog, tag=tag, date_begin=date_begin, date_end=date_end)

        search_string = opt.get('search', None)

        blog_posts = blog_post.search([('name', 'ilike', search_string)],
                                      offset=(page - 1) * self._blog_post_per_page,
                                      limit=self._blog_post_per_page) if search_string \
            else blog_post.search(domain,
                                  order="post_date desc")

        pager = request.website.pager(
            url=request.httprequest.path.partition('/page/')[0],
            total=len(blog_posts),
            page=page,
            step=self._blog_post_per_page,
            url_args=opt,
        )
        pager_begin = (page - 1) * self._blog_post_per_page
        pager_end = page * self._blog_post_per_page
        blog_posts = blog_posts[pager_begin:pager_end]

        all_tags = request.env['blog.tag'].search([])
        use_cover = request.website.viewref('website_blog.opt_blog_cover_post').active
        fullwidth_cover = request.website.viewref('website_blog.opt_blog_cover_post_fullwidth_design').active
        offset = (page - 1) * self._blog_post_per_page
        first_post = blog_posts
        if not blog:
            first_post = blog_posts.search(domain + [('website_published', '=', True)], order="post_date desc, id asc",
                                           limit=1)
            if use_cover and not fullwidth_cover:
                offset += 1

        # function to create the string list of tag ids, and toggle a given one.
        # used in the 'Tags Cloud' template.

        def tags_list(tag_ids, current_tag):
            tag_ids = list(tag_ids)  # required to avoid using the same list
            if current_tag in tag_ids:
                tag_ids.remove(current_tag)
            else:
                tag_ids.append(current_tag)
            tag_ids = request.env['blog.tag'].browse(tag_ids).exists()
            return ','.join(slug(tags) for tags in tag_ids)

        tag_category = sorted(all_tags.mapped('category_id'), key=lambda category: category.name.upper())
        other_tags = sorted(all_tags.filtered(lambda x: not x.category_id), key=lambda tags: tags.name.upper())
        values = {
            'blog': blog,
            'blogs': blogs,
            'first_post': first_post.with_prefetch(blog_posts.ids) if not search_string else None,
            'other_tags': other_tags,
            'state_info': {"state": state, "published": published_count, "unpublished": unpublished_count},
            'active_tag_ids': active_tag_ids,
            'tags_list': tags_list,
            'posts': blog_posts,
            'blog_posts_cover_properties': [json.loads(b.cover_properties) for b in blog_posts],
            'pager': pager,
            'nav_list': self.nav_list(blog),
            'blog_url': blog_url,
            'date': date_begin,
            'tag_category': tag_category,
        }
        response = request.render("website_blog.blog_post_short", values)
        return response

    @http.route('/blog/search', csrf=False, type="http", methods=['POST', 'GET'], auth="public", website=True)
    def search_contents(self, **kw):
        """get search result for auto suggestions"""
        strings = '%' + kw.get('name') + '%'
        try:
            domain = [('website_published', '=', True)]
            blog = request.env['blog.post'].with_user(SUPERUSER_ID).search(domain)
            sql = """select id as res_id, name as name, name as value from blog_post where name ILIKE '{}'"""
            extra_query = ''
            limit = " limit 15"
            qry = sql + extra_query + limit
            request.cr.execute(qry.format(strings, tuple(blog and blog.ids)))
            name = request.cr.dictfetchall()
        except:
            name = {'name': 'None', 'value': 'None'}
        return json.dumps(name)
