# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestThemeUtils(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].get_current_website()
        cls.theme_utils = cls.env['theme.utils'].with_context(
            website_id=cls.website.id)

    def test_post_copy_runs(self):
        """Whole hook runs without error and sets the logo."""
        self.theme_utils._theme_petzen_post_copy(None)
        self.assertTrue(self.website.logo)

    def test_enable_shop_views(self):
        self.theme_utils._petzen_enable_shop_views()
        view = self.env.ref('website_sale.search', raise_if_not_found=False)
        if view:
            self.assertTrue(view.with_context(
                website_id=self.website.id).active)

    def test_setup_header(self):
        self.theme_utils._petzen_setup_header()
        self.assertTrue(self.website.logo)

    def test_homepage_overlay(self):
        page = self.env['website.page'].search(
            [('url', '=', '/'), ('website_id', '=', self.website.id)],
            limit=1)
        self.theme_utils._petzen_setup_header()
        if page and 'header_overlay' in page._fields:
            self.assertTrue(page.header_overlay)
