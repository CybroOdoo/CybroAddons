# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from types import SimpleNamespace
from unittest.mock import Mock, patch

from odoo.exceptions import ValidationError
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
        config.set_param("dropbox_integration.client_id", "client-id")
        config.set_param("dropbox_integration.client_secret", "client-secret")
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

    def test_set_dropbox_refresh_token_creates_dashboard_credentials(self):
        config = self.env["ir.config_parameter"].sudo()
        config.set_param("dropbox_integration.client_id", "client-id")
        config.set_param("dropbox_integration.client_secret", "client-secret")
        oauth_flow = Mock()
        oauth_flow.finish.return_value = SimpleNamespace(
            refresh_token="refresh-token",
            access_token="access-token",
        )

        with patch(
            "odoo.addons.dropbox_integration.models.res_config_settings."
            "dropbox.oauth.DropboxOAuth2FlowNoRedirect",
            return_value=oauth_flow,
        ):
            self.env["res.config.settings"].set_dropbox_refresh_token("auth-code")

        dashboard = self.env["dropbox.dashboard"].search(
            [("dropbox_refresh_token", "=", "refresh-token")], limit=1
        )
        self.assertTrue(dashboard)
        self.assertEqual(dashboard.dropbox_client_id, "client-id")
        self.assertEqual(dashboard.dropbox_client_secret, "client-secret")
        self.assertEqual(dashboard.dropbox_access_token, "access-token")
        oauth_flow.finish.assert_called_once_with("auth-code")

    def test_set_dropbox_refresh_token_raises_validation_error_on_failure(self):
        with patch(
            "odoo.addons.dropbox_integration.models.res_config_settings."
            "dropbox.oauth.DropboxOAuth2FlowNoRedirect",
            side_effect=RuntimeError("invalid code"),
        ):
            with self.assertRaisesRegex(ValidationError, "Failed to Connect"):
                self.env["res.config.settings"].set_dropbox_refresh_token("bad-code")
