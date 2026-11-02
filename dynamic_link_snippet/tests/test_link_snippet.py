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

from odoo.modules.module import get_manifest
from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tools import file_path

MODULE = 'dynamic_link_snippet'


@tagged('post_install', '-at_install')
class TestSnippetTemplate(TransactionCase):
    """Check that the snippet is wired into the website builder."""

    def test_snippet_template_content(self):
        html = str(self.env['ir.qweb']._render('dynamic_link_snippet.link_snippet'))
        self.assertIn('s_dynamic_link', html)
        self.assertIn('s_dynamic_link_frame', html)

    def test_snippet_is_listed_in_builder(self):
        view = self.env.ref('dynamic_link_snippet.external_website_snippets')
        self.assertEqual(view.inherit_id, self.env.ref('website.snippets'))
        self.assertIn('dynamic_link_snippet.link_snippet', view.arch)
        self.assertTrue(view.active)

    def test_snippet_thumbnail_exists(self):
        view = self.env.ref('dynamic_link_snippet.external_website_snippets')
        self.assertIn('/dynamic_link_snippet/static/src/img/link.png', view.arch)
        self.assertTrue(file_path('dynamic_link_snippet/static/src/img/link.png'))


@tagged('post_install', '-at_install')
class TestAssets(TransactionCase):
    """Check that the JavaScript files of the snippet are shipped."""

    def test_assets_are_declared(self):
        assets = get_manifest(MODULE)['assets']
        self.assertIn('web.assets_frontend', assets)
        self.assertIn('website.website_builder_assets', assets)

    def test_assets_files_exist(self):
        for path in (
            'static/src/interactions/dynamic_link.js',
            'static/src/builder/dynamic_link_option.js',
            'static/src/builder/dynamic_link_option_plugin.js',
            'static/src/builder/dynamic_link_option.xml',
        ):
            self.assertTrue(file_path('%s/%s' % (MODULE, path)), path)


@tagged('post_install', '-at_install')
class TestSnippetTour(HttpCase):
    """Drive the website builder: insert the snippet and set its link."""

    def test_dynamic_link_snippet_tour(self):
        self.start_tour(
            self.env['website'].get_client_action_url('/', True),
            'dynamic_link_snippet_tour',
            login='admin',
        )
