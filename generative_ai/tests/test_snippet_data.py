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

from markupsafe import Markup

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWebsiteSnippetData(TransactionCase):
    """Tests for the stored AI generated snippets."""

    def test_get_content_returns_markup(self):
        snippet = self.env['website.snippet.data'].create({
            'name': 'Hero',
            'content': '<div class="hero"><h1>Hello</h1></div>',
            'is_ai_generated': True,
        })
        content = snippet.get_content()
        self.assertIsInstance(content, Markup)
        self.assertIn('<h1>Hello</h1>', content)

    def test_ai_generated_snippets_are_searchable(self):
        snippet = self.env['website.snippet.data'].create({
            'name': 'Banner',
            'content': '<p>Banner</p>',
            'is_ai_generated': True,
        })
        found = self.env['website.snippet.data'].search(
            [('is_ai_generated', '=', True), ('id', '=', snippet.id)])
        self.assertEqual(found, snippet)

    def test_snippet_default_is_not_ai_generated(self):
        snippet = self.env['website.snippet.data'].create({
            'name': 'Manual',
            'content': '<p>Manual</p>',
        })
        self.assertFalse(snippet.is_ai_generated)
