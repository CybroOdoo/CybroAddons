# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import tagged

from .common import ThemeHttpCommon


@tagged('post_install', '-at_install', 'theme_eco_refine')
class TestBlog(ThemeHttpCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.blog = cls.env['blog.blog'].create({'name': 'Eco Blog'})
        cls.post = cls.env['blog.post'].create({
            'name': 'Eco Post',
            'blog_id': cls.blog.id,
            'is_published': True,
            'content': '<p>Hello</p>',
        })

    def _post_url(self):
        slug = self.env['ir.http']._slug
        return '/blog/%s/%s' % (slug(self.blog), slug(self.post))

    def test_blog_index(self):
        self._get_html('/blog')

    def test_blog_post_page(self):
        page = self._get_html(self._post_url())
        self.assertIn('Eco Post', page.text_content())

    def test_blog_post_counts_a_visit(self):
        self._get_html(self._post_url())
        self.post.invalidate_recordset(['visits'])
        self.assertEqual(self.post.visits, 1)