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
            config.set_str(key, "value")

        uninstall_hook(self.env)

        for key in keys:
            self.assertFalse(config.search([("key", "=", key)]))
