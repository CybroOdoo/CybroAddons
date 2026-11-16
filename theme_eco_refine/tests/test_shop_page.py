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
from odoo.tests import tagged

from .common import ThemeHttpCommon


@tagged('post_install', '-at_install', 'theme_eco_refine')
class TestShopPage(ThemeHttpCommon):

    def test_shop_lists_published_product(self):
        page = self._get_html('/shop')
        self.assertIn('Eco Test Product', page.text_content())

    def test_shop_renders_with_custom_columns(self):
        """With `select` on, the shop uses the website's ppg / ppr."""
        website = self.website
        website.write({'select': True, 'shop_ppg': 6, 'shop_ppr': 3})
        self._get_html('/shop')