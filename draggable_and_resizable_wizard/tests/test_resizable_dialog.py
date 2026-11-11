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
from odoo.tools.misc import file_path

MODULE = 'draggable_and_resizable_wizard'
BACKEND_FILES = (
    f'{MODULE}/static/src/dialog/resizable_dialog.js',
    f'{MODULE}/static/src/dialog/resizable_dialog.xml',
    f'{MODULE}/static/src/dialog/resizable_dialog.scss',
)


@tagged('post_install', '-at_install')
class TestResizableDialogAssets(TransactionCase):
    """The Hoot tests in static/tests run through web's WebSuite for this module."""

    def test_files_are_in_the_backend_bundle(self):
        """The manifest paths exist and reach the backend bundle."""
        paths = [path for path, *_ in self.env['ir.asset']._get_asset_paths('web.assets_backend', {})]
        for asset in BACKEND_FILES:
            self.assertTrue(file_path(asset), asset)
            self.assertTrue(any(path.endswith(asset) for path in paths), f"{asset} is not in web.assets_backend")

    def test_tests_are_in_the_unit_test_bundle(self):
        paths = [path for path, *_ in self.env['ir.asset']._get_asset_paths('web.assets_unit_tests', {})]
        self.assertTrue(any(path.endswith(f'{MODULE}/static/tests/resizable_dialog.test.js') for path in paths))

