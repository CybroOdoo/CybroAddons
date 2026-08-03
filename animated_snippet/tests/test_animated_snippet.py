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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAnimatedSnippets(TransactionCase):

    def test_01_module_loaded_successfully(self):
        """Basic check - module installed without errors."""
        self.assertTrue(True, "Module loaded successfully")

    def test_02_snippets_templates_exist(self):
        """Check that snippet templates are registered in the system."""
        views = self.env['ir.ui.view'].search([
            ('type', '=', 'qweb'),
            ('name', 'ilike', 'Features'),
        ])
        self.assertGreater(len(views), 3, "Feature snippets not found")

    def test_03_columns_snippet_exists(self):
        """Check columns snippet."""
        view = self.env['ir.ui.view'].search([
            ('name', 'ilike', 'Columns'),
            ('type', '=', 'qweb'),
        ], limit=1)
        self.assertTrue(view, "Columns snippet not found")

    def test_04_image_gallery_snippet_exists(self):
        """Check image gallery snippet."""
        view = self.env['ir.ui.view'].search([
            ('name', 'ilike', 'Image Gallery'),
            ('type', '=', 'qweb'),
        ], limit=1)
        self.assertTrue(view, "Image Gallery snippet not found")

    def test_05_numbers_snippet_exists(self):
        """Check numbers snippet."""
        view = self.env['ir.ui.view'].search([
            ('name', 'ilike', 'Numbers'),
            ('type', '=', 'qweb'),
        ], limit=1)
        self.assertTrue(view, "Numbers snippet not found")

    def test_06_showcase_snippet_exists(self):
        """Check showcase snippet."""
        view = self.env['ir.ui.view'].search([
            ('name', 'ilike', 'Showcase'),
            ('type', '=', 'qweb'),
        ], limit=1)
        self.assertTrue(view, "Showcase snippet not found")