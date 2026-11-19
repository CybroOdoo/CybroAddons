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

from lxml import html

from odoo.tests import HttpCase


class ClassicStoreHttpCase(HttpCase):
    """Base class: applies the theme on a website and creates test data."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        theme = cls.env['ir.module.module'].search(
            [('name', '=', 'theme_classic_store')], limit=1)
        # Same steps as "Use this theme" in the website app.
        cls.website.theme_id = theme
        theme._theme_load(cls.website)
        cls.env['theme.utils'].with_context(
            website_id=cls.website.id)._post_copy(theme)

        cls.category = cls.env['product.public.category'].create({
            'name': 'ClassicStoreTest Category',
        })
        cls.product = cls.env['product.template'].create({
            'name': 'ClassicStoreTest Product',
            'list_price': 123.0,
            'sale_ok': True,
            'is_published': True,
            'public_categ_ids': [(6, 0, cls.category.ids)],
        })

    def get_html(self, url, **kwargs):
        """Open `url`, assert HTTP 200 and return the parsed document."""
        response = self.url_open(url, **kwargs)
        self.assertEqual(
            response.status_code, 200,
            f"{url} returned HTTP {response.status_code}")
        return html.fromstring(response.content)
