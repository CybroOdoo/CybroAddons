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

"""Tests for the Hue Backend Theme settings, company model and assets."""
import base64

from lxml import html

from odoo import Command
from odoo.tests import HttpCase, TransactionCase, tagged

# 1x1 PNG. Odoo 20 Binary fields reject raw ``bytes`` on write, so the image
# is passed as a base64 *string*; the raw bytes are only used to compare.
PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGA"
    "hKmMIQAAAABJRU5ErkJggg=="
)
PNG_BYTES = base64.b64decode(PNG_B64)

# Settings *field name* -> ir.config_parameter suffix -> key returned by
# config_color_settings().  Note the field is ``app_bar_color`` while the
# parameter and the returned key are ``appbar_color``.
COLOR_MAP = {
    # field name:      (parameter suffix,      returned key)
    "app_bar_color": ("appbar_color", "appbar_color"),
    "primary_accent": ("primary_accent_color", "primary_accent"),
    "kanban_bg_color": ("kanban_bg_color", "kanban_bg_color"),
    "primary_hover": ("primary_hover", "primary_hover"),
    "light_hover": ("light_hover", "light_hover"),
    "appbar_text": ("appbar_text", "appbar_text"),
    "appbar_hover": ("appbar_hover", "appbar_hover"),
}

DEFAULT_COLORS = {
    "app_bar_color": "#000000",
    "primary_accent": "#A53860",
    "kanban_bg_color": "#F7F7F7",
    "primary_hover": "#953256",
    "light_hover": "#d5d5d5",
    "appbar_text": "#F7F8F7",
    "appbar_hover": "#953256",
}

CUSTOM_COLORS = {
    "app_bar_color": "#111111",
    "primary_accent": "#223344",
    "kanban_bg_color": "#EEEEEE",
    "primary_hover": "#334455",
    "light_hover": "#CCCCCC",
    "appbar_text": "#FAFAFA",
    "appbar_hover": "#445566",
}

COLOR_KEYS = {
    "full_bg_img", "appbar_color", "primary_accent", "secondary_color",
    "kanban_bg_color", "primary_hover", "light_hover", "appbar_text",
    "appbar_hover",
}

# Fields that are shown in res_config_settings_views.xml.
# ``light_hover`` is a setting but has no input in the view.
FORM_FIELDS = (
    "theme_background", "app_bar_color", "appbar_text", "appbar_hover",
    "primary_accent", "kanban_bg_color", "primary_hover",
)


@tagged("post_install", "-at_install")
class TestHueThemeModels(TransactionCase):
    """Verify settings defaults, persistence and company background image."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Start every test from a clean state (no saved theme parameters).
        cls.env["ir.config_parameter"].search(
            [("key", "=like", "hue_backend_theme.%")]).unlink()
        cls.settings_model = cls.env["res.config.settings"]
        cls.admin = cls.env.ref("base.user_admin")
        cls.company = cls.admin.company_id

    def _background_attachment(self, company):
        return self.env["ir.attachment"].search([
            ("res_model", "=", "res.company"),
            ("res_field", "=", "background_image"),
            ("res_id", "=", company.id),
        ])

    def _assert_png_attachment(self, attachment):
        """Check the stored image without reading its content.

        In Odoo 20 ``attachment.raw`` returns a BinaryValue (here a
        LocalBinaryFile), not ``bytes``, so compare plain stored fields.
        """
        self.assertEqual(attachment.file_size, len(PNG_BYTES))
        self.assertEqual(attachment.mimetype, "image/png")

    def test_default_colors(self):
        """Settings expose the documented default colors."""
        defaults = self.settings_model.default_get(list(DEFAULT_COLORS))
        for field_name, expected in DEFAULT_COLORS.items():
            self.assertEqual(defaults[field_name], expected, field_name)

    def test_color_settings_are_saved_as_config_parameters(self):
        """Executing the settings stores each color in ir.config_parameter."""
        self.settings_model.create(CUSTOM_COLORS).execute()
        # Odoo 20 removed get_param(); typed getters (get_str...) replace it.
        params = self.env["ir.config_parameter"].sudo()
        for field_name, (suffix, _key) in COLOR_MAP.items():
            self.assertEqual(
                params.get_str(f"hue_backend_theme.{suffix}"),
                CUSTOM_COLORS[field_name],
                field_name,
            )

    def test_config_color_settings_returns_all_keys(self):
        """The color helper returns every key the frontend relies on."""
        colors = self.settings_model.config_color_settings()
        self.assertEqual(set(colors), COLOR_KEYS)

    def test_config_color_settings_reflects_saved_values(self):
        """Saved colors are what the color helper returns."""
        self.settings_model.create(CUSTOM_COLORS).execute()
        colors = self.settings_model.config_color_settings()
        for field_name, (_suffix, key) in COLOR_MAP.items():
            self.assertEqual(colors[key], CUSTOM_COLORS[field_name], field_name)

    def test_background_image_is_stored_as_attachment(self):
        """The company background image uses attachment storage."""
        self.company.background_image = PNG_B64
        attachment = self._background_attachment(self.company)
        self.assertEqual(len(attachment), 1)
        self._assert_png_attachment(attachment)
        self.assertTrue(self.company.background_image)

    def test_theme_background_writes_to_company(self):
        """The settings field is related to the company background image."""
        self.settings_model.create({"theme_background": PNG_B64}).execute()
        attachment = self._background_attachment(self.company)
        self.assertEqual(len(attachment), 1)
        self._assert_png_attachment(attachment)

    def test_full_bg_img_without_image(self):
        """No URL is returned when the company has no background image."""
        self.company.background_image = False
        colors = self.settings_model.with_user(self.admin).config_color_settings()
        self.assertFalse(colors["full_bg_img"])

    def test_full_bg_img_with_image(self):
        """A company image gives the /web/image URL for that company."""
        self.company.background_image = PNG_B64
        colors = self.settings_model.with_user(self.admin).config_color_settings()
        self.assertEqual(
            colors["full_bg_img"],
            f"/web/image/res.company/{self.company.id}/background_image",
        )

    def test_full_bg_img_is_per_company(self):
        """The URL follows the current user's company."""
        other_company = self.env["res.company"].create({
            "name": "Hue Other Company",
            "background_image": PNG_B64,
        })
        user = self.env["res.users"].create({
            "name": "Hue Theme User",
            "login": "hue_theme_user",
            "company_id": other_company.id,
            "company_ids": [Command.set(other_company.ids)],
        })
        colors = self.settings_model.with_user(user).config_color_settings()
        self.assertEqual(
            colors["full_bg_img"],
            f"/web/image/res.company/{other_company.id}/background_image",
        )

    def test_settings_form_contains_theme_fields(self):
        """The settings view exposes the theme fields."""
        arch = self.settings_model.get_view(view_type="form")["arch"]
        for field_name in FORM_FIELDS:
            self.assertIn(f'name="{field_name}"', arch, field_name)


@tagged("post_install", "-at_install")
class TestHueThemeHttp(HttpCase):
    """Verify asset bundles and the color RPC through real HTTP requests."""

    def _call_rpc(self, path, **params):
        response = self.url_open(path, json={
            "jsonrpc": "2.0",
            "method": "call",
            "id": 1,
            "params": params,
        })
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotIn("error", payload)
        return payload["result"]

    def _assert_bundles_load(self, page_path):
        response = self.url_open(page_path)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        urls = tree.xpath("//link[@rel='stylesheet']/@href")
        urls += tree.xpath("//script[@src]/@src")
        bundles = [url for url in urls if "/web/assets/" in url]
        self.assertTrue(bundles, "No asset bundles found on " + page_path)
        for url in bundles:
            bundle = self.url_open(url)
            self.assertEqual(bundle.status_code, 200, url)
            self.assertTrue(bundle.content, url)

    def test_login_page_assets_compile(self):
        """The frontend bundle (login.scss) compiles and loads."""
        self._assert_bundles_load("/web/login")

    def test_backend_assets_compile(self):
        """The backend bundles (SCSS, JS, XML templates) compile and load."""
        self.authenticate("admin", "admin")
        self._assert_bundles_load("/odoo")

    def test_color_settings_rpc(self):
        """The color helper can be called over RPC with saved values."""
        self.env["res.config.settings"].create(CUSTOM_COLORS).execute()
        self.authenticate("admin", "admin")
        colors = self._call_rpc(
            "/web/dataset/call_kw/res.config.settings/config_color_settings",
            model="res.config.settings",
            method="config_color_settings",
            args=[],
            kwargs={},
        )
        self.assertEqual(set(colors), COLOR_KEYS)
        self.assertEqual(colors["primary_accent"], CUSTOM_COLORS["primary_accent"])
        self.assertEqual(colors["appbar_color"], CUSTOM_COLORS["app_bar_color"])

    def test_browser_backend_loads_with_theme(self):
        """The web client starts in Chrome with the theme assets active."""
        self.env["res.config.settings"].create(CUSTOM_COLORS).execute()
        self.browser_js(
            "/odoo",
            """
            (async () => {
                const response = await fetch(
                    '/web/dataset/call_kw/res.config.settings/config_color_settings',
                    {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            jsonrpc: '2.0', method: 'call', id: 1,
                            params: {
                                model: 'res.config.settings',
                                method: 'config_color_settings',
                                args: [], kwargs: {},
                            },
                        }),
                    },
                );
                const colors = (await response.json()).result;
                if (!colors || colors.primary_accent !== '#223344') {
                    throw new Error('Theme colors were not returned to the client');
                }
                console.log('test successful');
            })();
            """,
            login="admin",
            ready="document.body.classList.contains('o_web_client')",
            timeout=60,
        )