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


@tagged('post_install', '-at_install', 'theme_petzen')
class TestThemeUtils(TransactionCase):
    """Test the setup done when the theme is applied to a website."""

    @classmethod
    def setUpClass(cls):
        """Prepare the website and its home page."""
        super().setUpClass()
        cls.website = cls.env['website'].get_current_website()
        cls.utils = cls.env['theme.utils'].with_context(website_id=cls.website.id)

    def test_post_copy(self):
        """The post copy hook enables the shop views and sets up the header."""
        self.utils._theme_petzen_post_copy(self.env['ir.module.module'])
        self.assertTrue(self.website.logo)
        header = self.env['website'].viewref('website.template_header_default')
        self.assertTrue(header.active)

    def test_enable_shop_views(self):
        """The eCommerce views used by the Petzen shop are enabled."""
        self.utils._petzen_enable_shop_views()
        view = self.env['website'].with_context(website_id=self.website.id).viewref('website_sale.products_categories')
        self.assertTrue(view.active)

    def test_setup_header_overlay(self):
        """The home page gets the transparent header over the hero."""
        homepage = self.env['website.page'].search(
            [('url', '=', '/')] + self.website.website_domain(), order='website_id', limit=1)
        self.assertTrue(homepage)
        self.utils._petzen_setup_header()
        self.assertTrue(homepage.header_overlay)

    def test_setup_header_without_homepage(self):
        """The header setup still works when the website has no home page."""
        self.env['website.page'].search([('url', '=', '/')]).unlink()
        self.utils._petzen_setup_header()
        self.assertTrue(self.website.logo)
