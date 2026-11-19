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
#############################################################################
from types import SimpleNamespace
from unittest.mock import Mock, patch

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDropboxResConfigSettings(TransactionCase):

    def test_action_get_dropbox_auth_code_returns_authentication_wizard_action(self):
        settings = self.env["res.config.settings"].create({})

        action = settings.action_get_dropbox_auth_code()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["name"], "Dropbox Authorization Wizard")
        self.assertEqual(action["res_model"], "dropbox.authentication")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["context"], {"dropbox_auth": True})

    def test_get_dropbox_auth_url_uses_configured_credentials(self):
        config = self.env["ir.config_parameter"].sudo()
        config.set_str("dropbox_integration.client_id", "client-id")
        config.set_str("dropbox_integration.client_secret", "client-secret")
        oauth_flow = Mock()
        oauth_flow.start.return_value = "https://dropbox.test/oauth"

        with patch(
            "odoo.addons.dropbox_integration.models.res_config_settings."
            "dropbox.oauth.DropboxOAuth2FlowNoRedirect",
            return_value=oauth_flow,
        ) as oauth_mock:
            url = self.env["res.config.settings"].get_dropbox_auth_url()

        oauth_mock.assert_called_once_with(
            "client-id",
            "client-secret",
            token_access_type="offline",
        )
        self.assertEqual(url, "https://dropbox.test/oauth")

    def test_get_dropbox_auth_url_raises_validation_error_when_unconfigured(self):
        self.env["ir.config_parameter"].sudo().search([
            ("key", "in", ["dropbox_integration.client_id", "dropbox_integration.client_secret"])
        ]).unlink()
        with self.assertRaises(ValidationError):
            self.env["res.config.settings"].get_dropbox_auth_url()

    def test_set_dropbox_refresh_token_creates_dashboard_credentials(self):
        config = self.env["ir.config_parameter"].sudo()
        config.set_str("dropbox_integration.client_id", "client-id")
        config.set_str("dropbox_integration.client_secret", "client-secret")
        oauth_flow = Mock()
        oauth_flow.finish.return_value = SimpleNamespace(
            refresh_token="refresh-token",
        )

        with patch(
            "odoo.addons.dropbox_integration.models.res_config_settings."
            "dropbox.oauth.DropboxOAuth2FlowNoRedirect",
            return_value=oauth_flow,
        ):
            self.env["res.config.settings"].set_dropbox_refresh_token("auth-code")

        dashboard = self.env["dropbox.dashboard"].sudo().search([], order="id desc", limit=1)
        self.assertEqual(dashboard.dropbox_client_id, "client-id")
        self.assertEqual(dashboard.dropbox_client_secret, "client-secret")
        self.assertEqual(dashboard.dropbox_refresh_token, "refresh-token")

    def test_set_dropbox_refresh_token_raises_validation_error_on_failure(self):
        oauth_flow = Mock()
        oauth_flow.finish.side_effect = RuntimeError("oauth failed")

        with patch(
            "odoo.addons.dropbox_integration.models.res_config_settings."
            "dropbox.oauth.DropboxOAuth2FlowNoRedirect",
            return_value=oauth_flow,
        ):
            with self.assertRaises(ValidationError):
                self.env["res.config.settings"].set_dropbox_refresh_token("bad-code")

    def test_security_res_config_settings_restricted_from_non_admins(self):
        regular_user = self.env["res.users"].create({
            "name": "Standard Employee",
            "login": "standard_employee_res_config_test",
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        portal_user = self.env["res.users"].create({
            "name": "Portal User",
            "login": "portal_user_res_config_test",
            "group_ids": [(6, 0, [self.env.ref("base.group_portal").id])],
        })

        for user in [regular_user, portal_user]:
            user_env = self.env(user=user)
            settings = user_env["res.config.settings"]
            with self.assertRaises(AccessError):
                settings.action_get_dropbox_auth_code()
            with self.assertRaises(AccessError):
                settings.get_dropbox_auth_url()
            with self.assertRaises(AccessError):
                settings.set_dropbox_refresh_token("test-code")
