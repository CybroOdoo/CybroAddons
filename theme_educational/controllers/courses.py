# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo.addons.website_slides.controllers.main import WebsiteSlides


class SlidesTagFilterController(WebsiteSlides):

    def _update_recently_viewed_slides(self, channel_id):
        """ Store recently viewed slide channel IDs in session """
        raw_slides = request.session.get('recently_viewed_slides', [])

        if isinstance(raw_slides, str):
            slides = [int(i) for i in raw_slides.split(',') if i.isdigit()]
        elif isinstance(raw_slides, list):
            slides = [int(i) for i in raw_slides if str(i).isdigit()]
        else:
            slides = []

        if channel_id in slides:
            slides.remove(channel_id)
        slides.insert(0, channel_id)
        slides = slides[:5]  # Keep only latest 5

        request.session['recently_viewed_slides'] = slides
        request.session.modified = True

    @http.route(['/slides/<model("slide.channel"):channel>'],
                type='http', auth="public", website=True)
    def channel(self, channel, **kwargs):
        self._update_recently_viewed_slides(channel.id)
        return super(SlidesTagFilterController, self).channel(channel, **kwargs)

    @http.route(['/slides/slide/<model("slide.slide"):slide>'],
                type='http', auth="public", website=True)
    def slide(self, slide, **kwargs):
        if slide.channel_id:
            self._update_recently_viewed_slides(slide.channel_id.id)
        return super(SlidesTagFilterController, self).slide(slide, **kwargs)

    @http.route(
        ['/slides/all', '/slides/all/page/<int:page>', '/slides/all/tag/<string:slug_tags>',
         '/slides/all/tag/<string:slug_tags>/page/<int:page>'],
        type='http', auth="public", website=True, sitemap=True, readonly=True
    )
    def slides_channel_all(self, slide_category=None, slug_tags=None, page=1, my=False, **post):
        # ✅ Ensure page is always int (fix for querystring case)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1

        # ✅ Collect tag filters
        tag_ids = [
            int(x) for x in request.httprequest.args.getlist('tag_ids[]') if x.isdigit()
        ]

        per_page = 15
        offset = (page - 1) * per_page

        render_values = self.slides_channel_all_values(
            slide_category=slide_category, slug_tags=slug_tags, my=my, **post)

        # ✅ Load all tags
        all_tags = request.env['slide.channel.tag'].sudo().search([], order='name asc')

        # ✅ Get recently viewed
        raw_recently_viewed = request.session.get('recently_viewed_slides', [])
        if isinstance(raw_recently_viewed, str):
            recently_viewed_ids = [int(i) for i in raw_recently_viewed.split(',') if i.isdigit()]
        elif isinstance(raw_recently_viewed, list):
            recently_viewed_ids = [int(i) for i in raw_recently_viewed if str(i).isdigit()]
        else:
            recently_viewed_ids = []

        channels = request.env['slide.channel'].sudo().search([])

        # ✅ Apply tag filtering
        if tag_ids:
            filtered = channels.filtered(lambda c: set(tag_ids).intersection(c.tag_ids.ids))
            recently_viewed_channels = request.env['slide.channel'].sudo().browse(
                recently_viewed_ids
            ).filtered(lambda c: set(tag_ids).intersection(c.tag_ids.ids))
        else:
            filtered = channels
            recently_viewed_channels = request.env['slide.channel'].sudo().browse(recently_viewed_ids)

        # ✅ Pagination logic
        total_courses = len(filtered)
        paginated_courses = filtered[offset: offset + per_page]

        # ✅ Build pager with tag_ids + slug_tags preserved
        url_args = []
        if tag_ids:
            url_args += [('tag_ids[]', tid) for tid in tag_ids]
        if slug_tags:
            url_args.append(('slug_tags', slug_tags))

        pager = request.website.pager(
            url="/slides/all",
            total=total_courses,
            page=page,
            step=per_page,
            scope=7,
            url_args=url_args
        )

        render_values.update({
            'all_tags': all_tags,
            'tag_ids': tag_ids,
            'selected_tag_ids': tag_ids,
            'channels': paginated_courses,
            'recently_viewed_channels': recently_viewed_channels,
            'pager': pager,
        })

        return request.render('website_slides.courses_all', render_values)
