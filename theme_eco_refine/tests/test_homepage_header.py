# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import tagged

from .common import ThemeHttpCommon

HEADER = "//div[contains(concat(' ', normalize-space(@class), ' '), ' ref-header ')]"
ICONS = "//div[contains(concat(' ', normalize-space(@class), ' '), ' ref-header__icons ')]"


@tagged('post_install', '-at_install', 'theme_eco_refine')
class TestHomepageHeader(ThemeHttpCommon):

    def test_homepage_uses_custom_header(self):
        page = self._get_html('/')
        self.assertEqual(len(page.xpath(HEADER)), 1)
        self.assertIn('ReTech', page.text_content())

    def test_custom_header_has_cart_and_wishlist_once(self):
        page = self._get_html('/')
        self.assertEqual(
            len(page.xpath(ICONS + "//li[contains(@class, 'o_wsale_my_cart')]")), 1)
        self.assertEqual(
            len(page.xpath(ICONS + "//li[contains(@class, 'o_wsale_my_wish')]")), 1)