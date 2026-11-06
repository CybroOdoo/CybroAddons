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

from odoo.addons.generative_ai.controllers.generative_ai import (
    preprocess_ai_output,
)


@tagged('post_install', '-at_install')
class TestPreprocessAiOutput(TransactionCase):
    """Tests for the cleaning of the AI generated markup."""

    def test_code_fences_are_removed(self):
        result = preprocess_ai_output('```html\n<div>Hi</div>\n```')
        self.assertEqual(result, '<div>Hi</div>')

    def test_existing_style_tag_is_kept(self):
        text = '<style>.a { color: red; }</style><p>x</p>'
        self.assertEqual(preprocess_ai_output(text), text)

    def test_loose_css_is_wrapped_in_style_tag(self):
        result = preprocess_ai_output('.card { color: red; }\n<p>x</p>')
        self.assertIn('<style>', result)
        self.assertIn('.card { color: red; }', result)
        self.assertIn('<p>x</p>', result)

    def test_plain_html_is_unchanged(self):
        self.assertEqual(preprocess_ai_output('<p>x</p>'), '<p>x</p>')
