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

import dropbox

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDropboxDashboard(TransactionCase):

    def test_action_import_files_returns_false_without_dashboard_credentials(self):
        self.env["dropbox.dashboard"].search([]).unlink()

        result = self.env["dropbox.dashboard"].action_import_files()

        self.assertFalse(result)

    def test_action_import_files_returns_temporary_links_by_file_name(self):
        config = self.env["ir.config_parameter"].sudo()
        config.set_str("dropbox_integration.folder_id", "odoo")
        self.env["dropbox.dashboard"].create({
            "dropbox_client_id": "client-id",
            "dropbox_client_secret": "client-secret",
            "dropbox_refresh_token": "refresh-token",
        })
        dbx = Mock()
        file_a = SimpleNamespace(path_lower="/odoo/file-a.pdf", name="file-a.pdf")
        setattr(file_a, ".tag", "file")
        file_b = SimpleNamespace(path_lower="/odoo/file-b.pdf", name="file-b.pdf")
        setattr(file_b, ".tag", "file")
        dbx.files_list_folder.return_value = SimpleNamespace(
            entries=[file_a, file_b],
            has_more=False,
        )
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

    def test_action_import_files_handles_folders_and_pagination(self):
        config = self.env["ir.config_parameter"].sudo()
        config.set_str("dropbox_integration.folder_id", "/")
        self.env["dropbox.dashboard"].create({
            "dropbox_client_id": "client-id",
            "dropbox_client_secret": "client-secret",
            "dropbox_refresh_token": "refresh-token",
        })
        dbx = Mock()
        # Page 1 contains a folder and a file
        folder_item = dropbox.files.FolderMetadata(
            name="subfolder",
            path_lower="/subfolder",
            path_display="/subfolder",
        )
        file_item_1 = dropbox.files.FileMetadata(
            name="doc1.pdf",
            path_lower="/doc1.pdf",
            path_display="/doc1.pdf",
            id="id:1",
            client_modified=None,
            server_modified=None,
            rev="123456789",
            size=100,
        )
        # Page 2 contains another file where temporary link fails
        file_item_2 = dropbox.files.FileMetadata(
            name="doc2.pdf",
            path_lower="/doc2.pdf",
            path_display="/doc2.pdf",
            id="id:2",
            client_modified=None,
            server_modified=None,
            rev="987654321",
            size=200,
        )

        dbx.files_list_folder.return_value = SimpleNamespace(
            entries=[folder_item, file_item_1],
            has_more=True,
            cursor="cursor_123",
        )
        dbx.files_list_folder_continue.return_value = SimpleNamespace(
            entries=[file_item_2],
            has_more=False,
            cursor="cursor_456",
        )
        dbx.files_get_temporary_link.side_effect = [
            SimpleNamespace(
                metadata=SimpleNamespace(name="doc1.pdf"),
                link="https://dropbox.test/doc1.pdf",
            ),
            RuntimeError("Link generation failed"),
        ]

        with patch(
            "odoo.addons.dropbox_integration.models.dropbox_dashboard.dropbox.Dropbox",
            return_value=dbx,
        ):
            result = self.env["dropbox.dashboard"].action_import_files()

        dbx.files_list_folder.assert_called_once_with(path="")
        dbx.files_list_folder_continue.assert_called_once_with(cursor="cursor_123")
        self.assertEqual(dbx.files_get_temporary_link.call_count, 2)
        self.assertIn("subfolder", result)
        self.assertEqual(result["subfolder"], "https://www.dropbox.com/home/subfolder")
        self.assertEqual(result["doc1.pdf"], "https://dropbox.test/doc1.pdf")
        self.assertEqual(result["doc2.pdf"], "https://www.dropbox.com/home/doc2.pdf")

    def test_action_import_files_returns_exception_payload_on_dropbox_error(self):
        self.env["dropbox.dashboard"].create({
            "dropbox_client_id": "client-id",
            "dropbox_client_secret": "client-secret",
            "dropbox_refresh_token": "refresh-token",
        })
        error = dropbox.exceptions.DropboxException("dropbox unavailable")

        with patch(
            "odoo.addons.dropbox_integration.models.dropbox_dashboard.dropbox.Dropbox",
            side_effect=error,
        ):
            result = self.env["dropbox.dashboard"].action_import_files()

        self.assertEqual(result[0], "e")
        self.assertEqual(result[1], str(error))

    def test_security_dashboard_model_restricted_from_regular_users(self):
        regular_user = self.env["res.users"].create({
            "name": "Regular Employee",
            "login": "employee_test_security_unique",
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        env_user = self.env(user=regular_user)
        with self.assertRaises(AccessError):
            env_user["dropbox.dashboard"].search([])
        with self.assertRaises(AccessError):
            env_user["dropbox.dashboard"].create({
                "dropbox_client_id": "bad",
            })

    def test_security_action_import_files_restricted_from_portal_and_public_users(self):
        portal_user = self.env["res.users"].create({
            "name": "Portal User Test",
            "login": "portal_user_import_files_test",
            "group_ids": [(6, 0, [self.env.ref("base.group_portal").id])],
        })
        with self.assertRaises(AccessError):
            self.env(user=portal_user)["dropbox.dashboard"].action_import_files()
