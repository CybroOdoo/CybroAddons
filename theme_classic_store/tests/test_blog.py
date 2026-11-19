# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import tagged

from .common import ClassicStoreHttpCase


@tagged('post_install', '-at_install')
class TestClassicStoreBlog(ClassicStoreHttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.blog = cls.env['blog.blog'].create({'name': 'ClassicStoreTest Blog'})
        cls.env['blog.post'].create({
            'name': 'ClassicStoreTest Post',
            'blog_id': cls.blog.id,
            'is_published': True,
        })

    def test_blog_index_shows_banner(self):
        """The "Blog" banner is shown on the all-blogs page."""
        doc = self.get_html('/blog')
        self.assertTrue(
            doc.xpath("//section[contains(@class, 'banner_about')]"),
            "The theme banner should be displayed on /blog")

    def test_single_blog_has_no_banner(self):
        doc = self.get_html(f'/blog/{self.env["ir.http"]._slug(self.blog)}')
        self.assertFalse(
            doc.xpath("//section[contains(@class, 'banner_about')]"),
            "The banner must not replace the cover of a single blog")

    def test_blog_post_page_renders(self):
        post = self.env['blog.post'].search(
            [('name', '=', 'ClassicStoreTest Post')], limit=1)
        self.get_html(f'/blog/{self.env["ir.http"]._slug(self.blog)}/'
                      f'{self.env["ir.http"]._slug(post)}')
