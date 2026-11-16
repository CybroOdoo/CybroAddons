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
from odoo.tests.common import JsonRpcException

from .common import ThemeHttpCommon


@tagged('post_install', '-at_install', 'theme_eco_refine')
class TestShopConfig(ThemeHttpCommon):
    """Tests for the /shop/config/website JSON route."""

    def test_admin_can_change_config(self):
        website = self.website
        website.select = False
        self.authenticate('admin', 'admin')
        self.make_jsonrpc_request('/shop/config/website', {
            'shop_ppg': 9,
            'shop_ppr': 3,
        })
        website.invalidate_recordset()
        self.assertEqual(website.shop_ppg, 9)
        self.assertEqual(website.shop_ppr, 3)
        self.assertTrue(website.select)

    def test_unknown_options_are_ignored(self):
        website = self.website
        original_name = website.name
        self.authenticate('admin', 'admin')
        self.make_jsonrpc_request('/shop/config/website', {
            'name': 'Hacked', 'shop_ppr': 3})
        website.invalidate_recordset()
        self.assertEqual(website.name, original_name)

    def test_non_editor_is_rejected(self):
        self.env['res.users'].create({
            'name': 'Portal User',
            'login': 'eco_portal',
            'password': 'eco_portal',
            'group_ids': [(6, 0, [self.ref('base.group_portal')])],
        })
        self.authenticate('eco_portal', 'eco_portal')
        with self.assertRaises(JsonRpcException):
            self.make_jsonrpc_request('/shop/config/website', {'shop_ppr': 3})

    def test_empty_ppg_and_grid_columns(self):
        """An empty ppg falls back to 1 and the grid columns are cast to int."""
        website = self.website
        self.authenticate('admin', 'admin')
        self.make_jsonrpc_request('/shop/config/website', {
            'ppg': 0,
            'product_page_grid_columns': '3',
        })
        website.invalidate_recordset()
        self.assertEqual(website.product_page_grid_columns, 3)

    def test_only_unknown_options_write_nothing(self):
        """With no writable option, nothing is written."""
        website = self.website
        ppr = website.shop_ppr
        self.authenticate('admin', 'admin')
        self.make_jsonrpc_request('/shop/config/website', {'unknown': 1})
        website.invalidate_recordset()
        self.assertEqual(website.shop_ppr, ppr)