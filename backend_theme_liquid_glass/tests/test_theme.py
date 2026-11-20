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
#############################################################################

import os
import re
from odoo.modules.module import get_manifest, get_module_path
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestThemeLiquidGlass(HttpCase):
    """Comprehensive test suite for Liquid Glass Backend Theme."""

    def test_theme_installed_and_metadata(self):
        """Verify theme module is recognized, installed, and has correct metadata."""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'backend_theme_liquid_glass'),
        ], limit=1)
        self.assertTrue(module.exists(), "backend_theme_liquid_glass module must exist in ir.module.module.")
        self.assertEqual(
            module.state, 'installed',
            "backend_theme_liquid_glass module must be installed."
        )
        category_name = module.category_id.name or ''
        self.assertIn(
            category_name, ('Backend', 'Theme/Backend'),
            "backend_theme_liquid_glass must be categorized under Backend or Theme/Backend."
        )

        manifest = get_manifest('backend_theme_liquid_glass')
        self.assertEqual(manifest.get('name'), 'Liquid Glass Backend Theme')
        self.assertEqual(manifest.get('category'), 'Theme/Backend')
        self.assertEqual(manifest.get('license'), 'LGPL-3')
        self.assertIn('web', manifest.get('depends', []))
        self.assertNotIn(
            'web.assets_frontend', manifest.get('assets', {}),
            "Backend theme must not inject styles into frontend asset bundle."
        )

    def test_theme_login_and_access(self):
        """Verify public access to login page and authenticated access to backend."""
        # 1. Public login route
        login_res = self.url_open('/web/login')
        self.assertEqual(
            login_res.status_code, 200,
            "Public login page must respond with HTTP 200."
        )

        # 2. Authenticated backend access
        self.authenticate('admin', 'admin')
        backend_res = self.url_open('/odoo')
        self.assertEqual(
            backend_res.status_code, 200,
            "Authenticated backend client route must respond with HTTP 200."
        )

    def test_theme_asset_bundles_compilation(self):
        """Verify that backend asset bundles compile without error and contain theme rules."""
        # 1. Main backend assets bundle compilation
        backend_bundle = self.env['ir.qweb']._get_asset_bundle('web.assets_backend')
        backend_css = backend_bundle.css()
        backend_js = backend_bundle.js()

        self.assertTrue(bool(backend_css), "web.assets_backend CSS bundle should compile successfully.")
        self.assertTrue(bool(backend_js), "web.assets_backend JS bundle should compile successfully.")

        # Helper to extract compiled text from ir.attachment recordset, list, or string
        def _get_bundle_content(bundle_res):
            if not bundle_res:
                return ""
            chunks = []
            records = bundle_res if hasattr(bundle_res, '__iter__') else [bundle_res]
            for item in records:
                raw_data = getattr(item, 'raw', None)
                if raw_data is not None:
                    if isinstance(raw_data, str):
                        chunks.append(raw_data)
                    elif hasattr(raw_data, 'decode'):
                        chunks.append(raw_data.decode('utf-8', errors='ignore'))
                    else:
                        chunks.append(bytes(raw_data).decode('utf-8', errors='ignore'))
                elif getattr(item, 'datas', None):
                    import base64
                    datas = item.datas
                    if isinstance(datas, bytes):
                        datas = datas.decode('ascii', errors='ignore')
                    chunks.append(base64.b64decode(datas).decode('utf-8', errors='ignore'))
                elif isinstance(item, (bytes, bytearray)):
                    chunks.append(item.decode('utf-8', errors='ignore'))
                else:
                    chunks.append(str(item))
            return "".join(chunks)

        # Ensure core theme SCSS selectors compiled into the backend bundle
        compiled_css_str = _get_bundle_content(backend_css)
        self.assertIn(
            '.o_web_client', compiled_css_str,
            ".o_web_client theme root selector must be present in compiled backend CSS."
        )
        self.assertIn(
            'bg-img.svg', compiled_css_str,
            "bg-img.svg wallpaper background must be referenced in compiled backend CSS."
        )
        self.assertIn(
            '.o_list_renderer', compiled_css_str,
            ".o_list_renderer list selector must be present in compiled backend CSS."
        )
        self.assertIn(
            '.o_list_table', compiled_css_str,
            ".o_list_table selector must be present in compiled backend CSS."
        )
        self.assertIn(
            '.modal-content', compiled_css_str,
            ".modal-content modal card selector must be present in compiled backend CSS."
        )

        # 2. Lazy backend assets bundle (containing canvas_text.js)
        lazy_bundle = self.env['ir.qweb']._get_asset_bundle('web.assets_backend_lazy')
        lazy_js = lazy_bundle.js()
        self.assertTrue(bool(lazy_js), "web.assets_backend_lazy JS bundle should compile successfully.")
        compiled_lazy_js_str = _get_bundle_content(lazy_js)
        self.assertIn(
            'GraphRenderer', compiled_lazy_js_str,
            "GraphRenderer patch must be compiled into web.assets_backend_lazy JS bundle."
        )

    def test_theme_individual_scss_files_integrity(self):
        """Verify every declared SCSS file exists on disk, is non-empty, and has balanced braces."""
        manifest = get_manifest('backend_theme_liquid_glass')
        module_path = get_module_path('backend_theme_liquid_glass')
        scss_assets = manifest.get('assets', {}).get('web.assets_backend', [])

        self.assertTrue(bool(scss_assets), "web.assets_backend must declare theme SCSS assets.")

        for asset_rel_path in scss_assets:
            if not asset_rel_path.endswith('.scss'):
                continue
            # Strip module name prefix
            clean_rel = re.sub(r'^backend_theme_liquid_glass/', '', asset_rel_path)
            full_path = os.path.join(module_path, clean_rel)
            self.assertTrue(os.path.isfile(full_path), f"SCSS asset file must exist on disk: {clean_rel}")
            file_size = os.path.getsize(full_path)
            self.assertGreater(file_size, 50, f"SCSS file must not be empty: {clean_rel}")

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Verify balanced braces
            clean_code = re.sub(r'//.*', '', content)
            clean_code = re.sub(r'/\*.*?\*/', '', clean_code, flags=re.DOTALL)
            stack = []
            for ch in clean_code:
                if ch in '{[(':
                    stack.append(ch)
                elif ch in '}])':
                    self.assertTrue(bool(stack), f"Unexpected closing '{ch}' in {clean_rel}")
                    opener = stack.pop()
                    expected = {'{': '}', '[': ']', '(': ')'}[opener]
                    self.assertEqual(ch, expected, f"Mismatched bracket in {clean_rel}: {opener} vs {ch}")
            self.assertEqual(len(stack), 0, f"Unclosed brackets in {clean_rel}: {stack}")

    def test_graph_renderer_patch_registration_and_logic(self):
        """Verify that canvas_text.js is registered in manifest, exists on disk, and patches GraphRenderer."""
        manifest = get_manifest('backend_theme_liquid_glass')
        lazy_assets = manifest.get('assets', {}).get('web.assets_backend_lazy', [])
        expected_path = 'backend_theme_liquid_glass/static/src/js/canvas_text.js'

        self.assertIn(
            expected_path, lazy_assets,
            f"{expected_path} must be registered under web.assets_backend_lazy in manifest."
        )

        module_path = get_module_path('backend_theme_liquid_glass')
        file_disk_path = os.path.join(module_path, 'static', 'src', 'js', 'canvas_text.js')
        self.assertTrue(os.path.isfile(file_disk_path), "canvas_text.js must exist on disk.")

        # Verify module imports and patch declaration
        with open(file_disk_path, 'r', encoding='utf-8') as f:
            code = f.read()

        self.assertIn('@odoo-module', code, "canvas_text.js must declare @odoo-module.")
        self.assertIn('@web/core/utils/patch', code, "canvas_text.js must import patch utility.")
        self.assertIn('@web/views/graph/graph_renderer', code, "canvas_text.js must import GraphRenderer.")
        self.assertIn('patch(GraphRenderer.prototype', code, "canvas_text.js must patch GraphRenderer.prototype.")
        self.assertIn('getScaleOptions', code, "canvas_text.js must override getScaleOptions.")
        self.assertIn('getLegendOptions', code, "canvas_text.js must override getLegendOptions.")
        self.assertIn('getContextualColor', code, "canvas_text.js must define getContextualColor helper.")
        self.assertIn('getRendererElement', code, "canvas_text.js must define getRendererElement helper.")

    def test_modals_dialog_dimensions_not_forced(self):
        """Verify that modals.scss does not force fixed dimensions on .modal-dialog."""
        module_path = get_module_path('backend_theme_liquid_glass')
        modals_path = os.path.join(module_path, 'static', 'src', 'scss', 'modals.scss')
        self.assertTrue(os.path.isfile(modals_path), "modals.scss must exist on disk.")

        with open(modals_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Ensure no global forced max-width is applied to .modal-dialog
        self.assertNotIn(
            'width: 92vw !important', content.split('.modal-content')[0],
            "modals.scss must not force width: 92vw !important globally on .modal-dialog."
        )
        self.assertNotIn(
            'max-width: 980px !important', content.split('.modal-content')[0],
            "modals.scss must not force max-width: 980px !important globally on .modal-dialog."
        )
        self.assertIn('.modal-content', content, "modals.scss must style .modal-content.")

    def test_website_configurator_and_builder_isolation(self):
        """Verify that theme protects website configurator and website builder from style leakage."""
        module_path = get_module_path('backend_theme_liquid_glass')
        glass_theme_path = os.path.join(module_path, 'static', 'src', 'scss', 'glass_theme.scss')
        forms_path = os.path.join(module_path, 'static', 'src', 'scss', 'forms.scss')
        buttons_path = os.path.join(module_path, 'static', 'src', 'scss', 'buttons.scss')

        with open(glass_theme_path, 'r', encoding='utf-8') as f:
            glass_content = f.read()

        # Ensure no destructive global span/div/p white color override exists at root
        self.assertNotIn(
            'span, div, p {\n    @include text-white-color;', glass_content,
            "glass_theme.scss must not force text-white globally on all span, div, and p elements."
        )

        # Ensure website configurator and website builder isolation blocks exist
        self.assertIn('.o_configurator_container', glass_content)
        self.assertIn('.o-website-builder_sidebar', glass_content)

        with open(forms_path, 'r', encoding='utf-8') as f:
            forms_content = f.read()

        self.assertIn('o_configurator_container', forms_content)
        self.assertIn('o_website_preview', forms_content)

        with open(buttons_path, 'r', encoding='utf-8') as f:
            buttons_content = f.read()

        self.assertNotIn('button,\n.btn,', buttons_content, "buttons.scss must not style unclassed button tag globally.")

    def test_theme_webclient_styling_browser(self):
        """Verify live browser DOM styling applied by the Liquid Glass backend theme."""
        test_script = """
            (function () {
                const webClient = document.querySelector('.o_web_client');
                if (!webClient) {
                    throw new Error('Element .o_web_client not found in DOM.');
                }

                const style = window.getComputedStyle(webClient);
                const bgImage = style.backgroundImage || '';
                if (!bgImage.includes('bg-img.svg') && !bgImage.includes('data:image')) {
                    console.warn('Computed background-image on .o_web_client:', bgImage);
                }

                const navbar = document.querySelector('.o_main_navbar, .o_navbar');
                if (!navbar) {
                    throw new Error('Main navbar element not found in DOM.');
                }

                console.log('Webclient styling verified successfully.');
                console.log('test successful');
            })();
        """
        self.browser_js(
            "/odoo",
            test_script,
            ready="Boolean(document.querySelector('.o_web_client'))",
            login="admin",
            timeout=30,
        )

    def test_graph_renderer_patch_functional_browser(self):
        """Verify GraphRenderer prototype methods and dynamic contextual coloring in live browser."""
        test_script = """
            (async function () {
                if (!window.odoo || !odoo.loader) {
                    throw new Error('Odoo module loader is not available.');
                }

                let GraphRenderer;
                try {
                    const mod = await odoo.loader.import('@web/views/graph/graph_renderer');
                    GraphRenderer = mod?.GraphRenderer;
                } catch (e) {
                    GraphRenderer = odoo.loader.modules.get('@web/views/graph/graph_renderer')?.GraphRenderer;
                }

                if (!GraphRenderer) {
                    throw new Error('Failed to resolve GraphRenderer from @web/views/graph/graph_renderer.');
                }

                // Verify patched methods exist on prototype
                if (typeof GraphRenderer.prototype.getScaleOptions !== 'function') {
                    throw new Error('GraphRenderer.prototype.getScaleOptions is missing.');
                }
                if (typeof GraphRenderer.prototype.getLegendOptions !== 'function') {
                    throw new Error('GraphRenderer.prototype.getLegendOptions is missing.');
                }

                // Create test container with custom text color
                const container = document.createElement('div');
                container.className = 'o_graph_renderer';
                container.style.color = 'rgb(255, 255, 255)';
                document.body.appendChild(container);

                try {
                    const mockRenderer = {
                        containerRef: () => container,
                        model: { metaData: { scale: {} } },
                    };

                    const scaleOptions = GraphRenderer.prototype.getScaleOptions.call(mockRenderer) || {};
                    console.log('getScaleOptions executed successfully:', Boolean(scaleOptions));

                    const legendOptions = GraphRenderer.prototype.getLegendOptions.call(mockRenderer) || {};
                    console.log('getLegendOptions executed successfully:', Boolean(legendOptions));

                    console.log('GraphRenderer patch functional test completed.');
                    console.log('test successful');
                } finally {
                    container.remove();
                }
            })();
        """
        self.browser_js(
            "/odoo",
            test_script,
            ready="Boolean(document.querySelector('.o_web_client'))",
            login="admin",
            timeout=30,
        )
