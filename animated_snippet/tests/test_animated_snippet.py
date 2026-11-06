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


@tagged('post_install', '-at_install')
class TestAnimatedSnippets(TransactionCase):
    """Check that every animated snippet template is installed and
    registered in the website snippet panel."""

    SNIPPET_XMLIDS = [
        'a_features', 'a_features_01', 'a_features_02', 'a_features_03',
        'a_features_04', 'a_features_05', 'a_features_06', 'a_features_07',
        'a_features_08', 'a_features_09', 'a_columns', 'a_image_gallery',
        'a_color_blocks', 'a_showcase', 'a_numbers', 'a_product_list',
    ]

    def test_01_snippet_templates_exist(self):
        """Every snippet template is loaded as a QWeb view."""
        for xmlid in self.SNIPPET_XMLIDS:
            with self.subTest(snippet=xmlid):
                view = self.env.ref('animated_snippet.%s' % xmlid,
                                    raise_if_not_found=False)
                self.assertTrue(view, "Snippet '%s' not found" % xmlid)
                self.assertEqual(view.type, 'qweb')

    def test_02_snippets_registered_in_panel(self):
        """Every snippet is declared in the website snippet panel."""
        arch = self.env.ref('website.snippets').get_combined_arch()
        for xmlid in self.SNIPPET_XMLIDS:
            with self.subTest(snippet=xmlid):
                self.assertIn(
                    't-snippet="animated_snippet.%s"' % xmlid, arch,
                    "Snippet '%s' is not registered in the panel" % xmlid)

    def test_03_snippet_group_registered(self):
        """The Animated Snippets group is added to the snippet groups."""
        arch = self.env.ref('website.snippets').get_combined_arch()
        self.assertIn('snippet-group="animated_snippet"', arch)

    def test_04_snippets_render(self):
        """Every snippet template renders without error."""
        for xmlid in self.SNIPPET_XMLIDS:
            with self.subTest(snippet=xmlid):
                html = self.env['ir.qweb']._render(
                    'animated_snippet.%s' % xmlid)
                self.assertTrue(html, "Snippet '%s' rendered empty" % xmlid)
