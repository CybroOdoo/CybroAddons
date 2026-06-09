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

from odoo.tests import TransactionCase, tagged

from odoo.addons.dropbox_integration.hooks import uninstall_hook


@tagged("post_install", "-at_install")
class TestDropboxIntegrationHooks(TransactionCase):

    def test_uninstall_hook_removes_dropbox_config_parameters(self):
        config = self.env["ir.config_parameter"].sudo()
        keys = [
            "dropbox_integration.client_id",
            "dropbox_integration.client_secret",
            "dropbox_integration.folder_id",
            "dropbox_integration.dropbox_button",
        ]
        for key in keys:
            config.set_param(key, "value")

        uninstall_hook(self.env.cr)

        for key in keys:
            self.assertFalse(config.search([("key", "=", key)]))
