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
from lxml import html

from odoo.tests import HttpCase


class ThemeHttpCommon(HttpCase):
    """Shared data and helpers for the HTTP tests of theme_eco_refine."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        cls.env.ref('base.module_theme_eco_refine')._theme_load(cls.website)
        cls.category = cls.env['product.public.category'].create(
            {'name': 'Eco Category'})
        cls.product = cls.env['product.template'].create({
            'name': 'Eco Test Product',
            'list_price': 10.0,
            'is_published': True,
            'public_categ_ids': [(6, 0, cls.category.ids)],
        })

    def _get_html(self, url, **kwargs):
        """Open `url`, check for a 200 answer and return the parsed page."""
        response = self.url_open(url, **kwargs)
        self.assertEqual(response.status_code, 200, url)
        return html.fromstring(response.content)

    def _call_snippet(self, route):
        """Call a snippet JSON route.

        Each route returns [products, categories, website, <extra>].
        """
        result = self.make_jsonrpc_request(route, {})
        self.assertEqual(len(result), 4, route)
        return result