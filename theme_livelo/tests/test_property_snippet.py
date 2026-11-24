# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

from odoo.tests import common, tagged
from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.theme_livelo.controller.property_snippet import ThemeLiveloPropertySnippet


@tagged('post_install', '-at_install')
class TestPropertySnippet(common.HttpCase):
    """Test suite for the dynamic Property Snippet controller and QWeb rendering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].get_current_website()

        # Load theme templates onto the current website so QWeb can render them
        theme_module = cls.env['ir.module.module'].search([('name', '=', 'theme_livelo')])
        if theme_module:
            theme_module.with_context(load_all_views=True)._theme_load(cls.website)

        cls.snippet_controller = ThemeLiveloPropertySnippet()

        # Create distinct properties for each type if not already present
        property_types = ['apartment', 'villa', 'studio', 'house', 'office']
        for p_type in property_types:
            existing = cls.env['product.template'].search([
                ('is_property', '=', True),
                ('property_type', '=', p_type),
            ], limit=1)
            if not existing:
                cls.env['product.template'].create({
                    'name': f'Test {p_type.capitalize()} Snippet Property',
                    'is_property': True,
                    'is_featured': True,
                    'property_type': p_type,
                    'list_price': 5000.0,
                    'bed': 2,
                    'bath': 1,
                    'squarefeet': 1000,
                    'website_published': True,
                })

    def test_01_property_snippet_controller_direct(self):
        """Test invoking get_featured_properties controller method directly in MockRequest."""
        with MockRequest(self.env, website=self.website):
            res = self.snippet_controller.get_featured_properties()
            self.assertIsInstance(res, dict)
            self.assertIn('html', res)
            html = res['html']

            # Verify tab headers exist
            self.assertIn('prop_tab_all', html)
            self.assertIn('prop_tab_apt', html)
            self.assertIn('prop_tab_villa', html)
            self.assertIn('prop_tab_studio', html)
            self.assertIn('prop_tab_house', html)
            self.assertIn('prop_tab_office', html)

            # Verify navigation labels exist
            self.assertIn('View all', html)
            self.assertIn('Apartment', html)
            self.assertIn('Villa', html)
            self.assertIn('Studio', html)
            self.assertIn('House', html)
            self.assertIn('Office', html)

    def test_02_property_snippet_jsonrpc_endpoint(self):
        """Test calling /theme_livelo/get_featured_properties via JSON-RPC."""
        data = self.make_jsonrpc_request('/theme_livelo/get_featured_properties', {})
        self.assertIsInstance(data, dict, "Endpoint should return a dictionary")
        self.assertIn('html', data, "Returned dictionary should contain 'html'")
        html = data['html']

        # Ensure content is not empty and contains cards or tabs
        self.assertIn('s_property_tabs_row', html)
        self.assertIn('s_property_nav_tabs', html)
        self.assertIn('s_property_tab_content', html)

    def test_03_property_snippet_featured_order(self):
        """Test that featured properties are prioritized in the snippet output."""
        # Create non-featured and featured properties of a unique name
        self.env['product.template'].create({
            'name': 'AAA Non Featured Test Property',
            'is_property': True,
            'is_featured': False,
            'list_price': 1000.0,
            'website_published': True,
        })
        self.env['product.template'].create({
            'name': 'ZZZ Featured Test Property',
            'is_property': True,
            'is_featured': True,
            'list_price': 2000.0,
            'website_published': True,
        })

        with MockRequest(self.env, website=self.website):
            res = self.snippet_controller.get_featured_properties()
            html = res['html']
            self.assertIn('ZZZ Featured Test Property', html)
