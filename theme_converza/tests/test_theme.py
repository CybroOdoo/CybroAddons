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

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestConverzaTheme(TransactionCase):
    """Data loaded by the theme: pages, views and menu templates."""

    PAGES = {
        'theme_converza.about_us_page': '/aboutus',
        'theme_converza.case_study_page': '/case-studies',
        'theme_converza.pricing_page_record': '/pricing',
        'theme_converza.result_page_record': '/result',
        'theme_converza.services_page_record': '/services',
    }
    MENUS = {
        'theme_converza.theme_converza_menu_services': '/services',
        'theme_converza.theme_converza_menu_result': '/result',
        'theme_converza.theme_converza_menu_case_studies': '/case-studies',
        'theme_converza.theme_converza_menu_pricing': '/pricing',
    }

    def test_pages_are_published_with_expected_url(self):
        for xmlid, url in self.PAGES.items():
            page = self.env.ref(xmlid)
            self.assertEqual(page.url, url, xmlid)
            self.assertTrue(page.is_published, xmlid)
            self.assertTrue(page.view_id.active, xmlid)

    def test_menu_templates_exist(self):
        for xmlid, url in self.MENUS.items():
            menu = self.env.ref(xmlid)
            self.assertEqual(menu.url, url, xmlid)
            self.assertTrue(menu.name, xmlid)

    def test_menus_do_not_duplicate_core_entries(self):
        names = {self.env.ref(x).name for x in self.MENUS}
        for core in ('Home', 'Shop', 'Blog', 'Contact us'):
            self.assertNotIn(core, names)

    def test_theme_views_are_valid_qweb(self):
        views = self.env['ir.ui.view'].search([
            ('key', 'like', 'theme_converza.%'),
        ])
        self.assertTrue(views)
        for view in views:
            # Combined arch computation fails on a broken inheritance.
            self.assertTrue(view._get_combined_arch() is not None, view.key)


@tagged('post_install', '-at_install')
class TestConverzaPagesRender(HttpCase):
    """Public pages shipped by the theme render without server errors."""

    def test_public_pages_render(self):
        for url in ('/aboutus', '/case-studies', '/pricing', '/result',
                    '/services'):
            with self.subTest(url=url):
                response = self.url_open(url)
                self.assertEqual(response.status_code, 200, url)
