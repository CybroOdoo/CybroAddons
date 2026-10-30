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
#############################################################################
from odoo.modules.module import get_manifest
from odoo.tests.common import HttpCase, TransactionCase, tagged
from odoo.tools.misc import file_path


@tagged('post_install', '-at_install')
class TestOne2ManySearchWidget(TransactionCase):
    """Test suite for One2many Search Widget module."""

    def test_01_module_is_installed(self):
        """Verify that one2many_search_widget is installed."""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'one2many_search_widget'),
        ])
        self.assertTrue(module, "Module one2many_search_widget should exist in ir.module.module.")
        self.assertEqual(module.state, 'installed', "Module one2many_search_widget should be installed.")

    def test_02_manifest_assets_exist(self):
        """Verify that all assets declared in __manifest__.py exist and are non-empty."""
        manifest = get_manifest('one2many_search_widget')
        assets = manifest.get('assets', {}).get('web.assets_backend', [])
        self.assertTrue(assets, "Module must declare assets under web.assets_backend.")
        for asset_path in assets:
            resolved_path = file_path(asset_path)
            self.assertTrue(resolved_path, f"Asset path {asset_path} could not be resolved.")
            with open(resolved_path, 'rb') as asset_file:
                content = asset_file.read()
                self.assertGreater(len(content), 0, f"Asset file {asset_path} must not be empty.")

    def test_03_view_definition_with_widget(self):
        """Verify that a form view with widget='one2many_search' compiles and loads correctly."""
        partner_form_view = self.env['ir.ui.view'].create({
            'name': 'test.partner.one2many.search.view',
            'model': 'res.partner',
            'type': 'form',
            'arch': """
                <form string="Test Partner">
                    <sheet>
                        <field name="name"/>
                        <field name="child_ids" widget="one2many_search">
                            <list>
                                <field name="name"/>
                                <field name="email"/>
                            </list>
                        </field>
                    </sheet>
                </form>
            """,
        })
        view_description = self.env['res.partner'].get_view(partner_form_view.id, 'form')
        self.assertIn('one2many_search', view_description.get('arch', ''))
        self.assertIn('child_ids', view_description.get('models', {}).get('res.partner', {}))

    def test_04_assets_bundle_generation(self):
        """Verify that web.assets_backend compiles assets without error."""
        bundle_js = self.env['ir.qweb']._get_asset_bundle('web.assets_backend', js=True, css=False)
        self.assertTrue(bundle_js.javascripts, "web.assets_backend bundle must include javascript files.")
        bundle_css = self.env['ir.qweb']._get_asset_bundle('web.assets_backend', js=False, css=True)
        self.assertTrue(bundle_css.stylesheets, "web.assets_backend bundle must include stylesheets.")


@tagged('post_install', '-at_install')
class TestOne2ManySearchWidgetHttp(HttpCase):
    """HTTP integration tests for One2many Search Widget."""

    def test_01_static_assets_http(self):
        """Verify that widget static assets are served properly via HTTP."""
        response_js = self.url_open('/one2many_search_widget/static/src/fields/one2manysearch/one2manysearch.js')
        self.assertEqual(response_js.status_code, 200, "JS asset should be accessible via HTTP.")
        self.assertIn('one2many_search', response_js.text, "JS file content must contain widget definition.")

        response_css = self.url_open('/one2many_search_widget/static/src/css/header.css')
        self.assertEqual(response_css.status_code, 200, "CSS asset should be accessible via HTTP.")
        self.assertIn('.o_one2many_search_wrapper', response_css.text)

        response_xml = self.url_open('/one2many_search_widget/static/src/fields/one2manysearch/one2manysearch_template.xml')
        self.assertEqual(response_xml.status_code, 200, "XML template asset should be accessible via HTTP.")
        self.assertIn('One2ManySearchTemplate', response_xml.text)

    def test_02_web_client_access(self):
        """Verify that web client loads for authenticated internal user."""
        user = self.env.ref('base.user_admin', raise_if_not_found=False) or self.env['res.users'].search([
            ('share', '=', False),
            ('active', '=', True),
        ], limit=1)
        if user:
            self.authenticate(user.login, user.login)
            response = self.url_open('/web')
            self.assertEqual(response.status_code, 200, "Web client must load with status 200.")
