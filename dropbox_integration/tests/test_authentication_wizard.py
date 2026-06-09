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

from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.dropbox_integration.models.res_config_settings import (
    ResConfigSettings,
)


@tagged("post_install", "-at_install")
class TestDropboxAuthenticationWizard(TransactionCase):

    def test_compute_dropbox_auth_url_uses_active_config_settings(self):
        settings = self.env["res.config.settings"].create({})

        with patch.object(
            ResConfigSettings,
            "get_dropbox_auth_url",
            return_value="https://dropbox.test/oauth",
        ) as auth_url_mock:
            wizard = self.env["dropbox.authentication"].with_context(
                active_id=settings.id
            ).create({"dropbox_authorization_code": "auth-code"})
            wizard._compute_dropbox_auth_url()

        self.assertGreaterEqual(auth_url_mock.call_count, 1)
        self.assertEqual(wizard.dropbox_auth_url, "https://dropbox.test/oauth")

    def test_action_setup_dropbox_token_delegates_to_active_config_settings(self):
        settings = self.env["res.config.settings"].create({})

        with patch.object(
            ResConfigSettings,
            "get_dropbox_auth_url",
            return_value="https://dropbox.test/oauth",
        ), patch.object(
            ResConfigSettings,
            "set_dropbox_refresh_token",
            autospec=True,
        ) as set_token_mock:
            wizard = self.env["dropbox.authentication"].with_context(
                active_id=settings.id
            ).create({"dropbox_authorization_code": "auth-code"})
            wizard.action_setup_dropbox_token()

        set_token_mock.assert_called_once()
        self.assertEqual(set_token_mock.call_args.args[1], "auth-code")
