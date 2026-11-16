# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestThemeData(TransactionCase):

    def test_menus_created(self):
        expected = {
            'theme_velora.menu_collections': '/collections',
            'theme_velora.menu_shop': '/bestsellers',
            'theme_velora.menu_aboutus': '/about',
        }
        main_menu = self.env.ref('website.main_menu')
        for xml_id, url in expected.items():
            with self.subTest(menu=xml_id):
                menu = self.env.ref(xml_id)
                self.assertEqual(menu.url, url)
                self.assertEqual(menu.parent_id, main_menu)

    def test_fragrance_categories_created(self):
        names = {
            'mens': 'Men', 'womens': 'Women', 'unisex': 'Unisex',
            'floral': 'Floral', 'woody': 'Woody', 'fresh': 'Fresh', 'citrus': 'Citrus',
            'amber': 'Amber', 'musk': 'Musk', 'oriental': 'Oriental', 'aquatic': 'Aquatic',
        }
        for key, name in names.items():
            with self.subTest(category=key):
                category = self.env.ref(f'theme_velora.theme_velora_category_{key}')
                self.assertEqual(category.name, name)

    def test_theme_pages_published(self):
        for xml_id in ('page_about_theme', 'page_bestsellers_theme', 'page_collections_theme'):
            with self.subTest(page=xml_id):
                page = self.env.ref(f'theme_velora.{xml_id}')
                self.assertTrue(page.is_published)
                self.assertTrue(page.url.startswith('/'))
