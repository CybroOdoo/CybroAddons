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
from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path

MODULE = 'tree_view_advanced_search'


@tagged('post_install', '-at_install')
class TestTreeViewAdvancedSearch(TransactionCase):
    """Sanity tests for the module's manifest and installation state."""

    def test_module_is_installed(self):
        """The module must be in the installed state."""
        module = self.env['ir.module.module'].search(
            [('name', '=', MODULE)])
        self.assertEqual(module.state, 'installed')

    def test_dependencies_are_installed(self):
        """Every module listed in 'depends' must be installed."""
        depends = set(get_manifest(MODULE)['depends'])
        installed = self.env['ir.module.module'].search([
            ('name', 'in', list(depends)),
            ('state', '=', 'installed'),
        ])
        self.assertEqual(set(installed.mapped('name')), depends)

    def test_manifest_assets_exist(self):
        """Every file declared in the manifest assets must exist."""
        assets = get_manifest(MODULE)['assets']
        for bundle, paths in assets.items():
            for path in paths:
                if '*' in path:
                    continue
                self.assertTrue(
                    file_path(path),
                    "Asset %s from bundle %s is missing" % (path, bundle))
