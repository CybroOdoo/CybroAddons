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

from odoo.modules.module import get_manifest
from odoo.tests import tagged
from odoo.tests.common import HttpCase
from odoo.tools import file_path

PAGE_URLS = ['/services', '/result', '/case-studies', '/pricing', '/aboutus']
MENU_URLS = ['/services', '/result', '/case-studies', '/pricing', '/aboutus']
SNIPPETS = [
    's_marketing_snippets', 's_service_templates', 's_about_template',
    's_result_analytics', 's_process_template', 's_pricing_template',
    's_testimonials_template', 's_case_study_template', 's_team_template',
    's_insights_template', 's_contact_template',
]


@tagged('post_install', '-at_install')
class TestThemeConverza(HttpCase):
    """Checks the pages, menus, snippets and assets shipped by the theme."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref('website.default_website')
        cls.theme = cls.env['ir.module.module'].search(
            [('name', '=', 'theme_converza')], limit=1)
        cls.theme._theme_load(cls.website)

    def test_manifest_assets_are_local(self):
        """Every frontend asset must be shipped inside the module."""
        assets = get_manifest('theme_converza')['assets']['web.assets_frontend']
        for path in assets:
            with self.subTest(path=path):
                self.assertFalse(path.startswith(('http://', 'https://', '//')),
                                 "External assets must not be loaded from a CDN")
                self.assertTrue(file_path(path), "%s is missing" % path)

    def test_pages_are_created(self):
        pages = self.env['website.page'].search([
            ('website_id', '=', self.website.id),
            ('url', 'in', PAGE_URLS),
        ])
        self.assertEqual(set(pages.mapped('url')), set(PAGE_URLS))
        self.assertTrue(all(pages.mapped('is_published')))

    def test_menus_are_created(self):
        menus = self.env['website.menu'].search([
            ('website_id', '=', self.website.id),
            ('url', 'in', MENU_URLS),
        ])
        self.assertEqual(set(menus.mapped('url')), set(MENU_URLS))

    def test_snippet_templates_exist(self):
        for name in SNIPPETS:
            with self.subTest(snippet=name):
                view = self.env.ref('theme_converza.%s' % name)
                self.assertTrue(view.arch, "%s has no content" % name)

    def test_theme_pages_render(self):
        for url in ['/'] + PAGE_URLS + ['/contactus', '/blog']:
            with self.subTest(url=url):
                response = self.url_open(url)
                self.assertEqual(response.status_code, 200,
                                 "%s should render" % url)

    def test_header_footer_and_scope(self):
        html = self.url_open('/').text
        self.assertIn('cvz_header', html, "Custom header is missing")
        self.assertIn('cvz_footer', html, "Custom footer is missing")
        self.assertIn('cvz_scope', html, "Theme scope class is missing")

    def test_case_filter_tour(self):
        self.start_tour('/case-studies', 'theme_converza_case_filter')

    def test_pricing_toggle_tour(self):
        self.start_tour('/pricing', 'theme_converza_pricing_toggle')

    def test_counters_tour(self):
        self.start_tour('/result', 'theme_converza_counters')
