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

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestThemeFinverseWebsiteMenus(TransactionCase):
    """Ensure the Finverse website menu entries are installed correctly."""

    def test_website_menu_entries(self):
        expected_menus = {
            'theme_finverse.finverse_menu_about': ('About', '/about', 20),
            'theme_finverse.finverse_menu_services': (
                'Services', '/services', 30),
            'theme_finverse.finverse_menu_industries': (
                'Industries', '/industries', 40),
            'theme_finverse.finverse_menu_insights': (
                'Insights', '/insights', 50),
        }
        main_menu = self.env.ref('website.main_menu')

        for xmlid, (name, url, sequence) in expected_menus.items():
            with self.subTest(xmlid=xmlid):
                menu = self.env.ref(xmlid, raise_if_not_found=False)
                self.assertTrue(menu, 'Missing website menu: %s' % xmlid)
                self.assertEqual(menu.name, name)
                self.assertEqual(menu.url, url)
                self.assertEqual(menu.parent_id, main_menu)
                self.assertEqual(menu.sequence, sequence)
