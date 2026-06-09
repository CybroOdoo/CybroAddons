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

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDropboxDashboard(TransactionCase):

    def test_action_import_files_returns_false_without_dashboard_credentials(self):
        self.env["dropbox.dashboard"].search([]).unlink()

        result = self.env["dropbox.dashboard"].action_import_files()

        self.assertFalse(result)

    def test_action_import_files_returns_temporary_links_by_file_name(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "dropbox_integration.folder_id", "/odoo"
        )
        self.env["dropbox.dashboard"].create({
            "dropbox_client_id": "client-id",
            "dropbox_client_secret": "client-secret",
            "dropbox_refresh_token": "refresh-token",
        })
        dbx = Mock()
        dbx.files_list_folder.return_value = SimpleNamespace(entries=[
            SimpleNamespace(path_lower="/odoo/file-a.pdf"),
            SimpleNamespace(path_lower="/odoo/file-b.pdf"),
        ])
        dbx.files_get_temporary_link.side_effect = [
            SimpleNamespace(
                metadata=SimpleNamespace(name="file-a.pdf"),
                link="https://dropbox.test/a",
            ),
            SimpleNamespace(
                metadata=SimpleNamespace(name="file-b.pdf"),
                link="https://dropbox.test/b",
            ),
        ]

        with patch(
            "odoo.addons.dropbox_integration.models.dropbox_dashboard.dropbox.Dropbox",
            return_value=dbx,
        ) as dropbox_mock:
            result = self.env["dropbox.dashboard"].action_import_files()

        dropbox_mock.assert_called_once_with(
            app_key="client-id",
            app_secret="client-secret",
            oauth2_refresh_token="refresh-token",
        )
        dbx.files_list_folder.assert_called_once_with(path="/odoo")
        self.assertEqual(
            result,
            {
                "file-a.pdf": "https://dropbox.test/a",
                "file-b.pdf": "https://dropbox.test/b",
            },
        )

    def test_action_import_files_returns_exception_payload_on_dropbox_error(self):
        self.env["dropbox.dashboard"].create({
            "dropbox_client_id": "client-id",
            "dropbox_client_secret": "client-secret",
            "dropbox_refresh_token": "refresh-token",
        })
        error = RuntimeError("dropbox unavailable")

        with patch(
            "odoo.addons.dropbox_integration.models.dropbox_dashboard.dropbox.Dropbox",
            side_effect=error,
        ):
            result = self.env["dropbox.dashboard"].action_import_files()

        self.assertEqual(result[0], "e")
        self.assertIs(result[1], error)
