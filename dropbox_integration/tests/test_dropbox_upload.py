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
import base64
from unittest.mock import patch

import dropbox

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDropboxUpload(TransactionCase):

    def test_action_upload_file_uploads_attachment_to_configured_folder(self):
        config = self.env["ir.config_parameter"].sudo()
        config.set_str("dropbox_integration.folder_id", "/odoo")
        self.env["dropbox.dashboard"].create({
            "dropbox_client_id": "client-id",
            "dropbox_client_secret": "client-secret",
            "dropbox_refresh_token": "refresh-token",
        })
        wizard = self.env["dropbox.upload"].create({"file_name": "report.pdf"})
        self.env["ir.attachment"].create({
            "name": "report.pdf",
            "type": "binary",
            "raw": b"report content",
            "res_model": "dropbox.upload",
            "res_id": wizard.id,
        })

        with patch(
            "odoo.addons.dropbox_integration.wizard.dropbox_upload.dropbox.Dropbox"
        ) as dropbox_mock:
            result = wizard.action_upload_file()

        dropbox_mock.assert_called_once_with(
            app_key="client-id",
            app_secret="client-secret",
            oauth2_refresh_token="refresh-token",
        )
        dropbox_mock.return_value.files_upload.assert_called_once_with(
            b"report content", "/odoo/report.pdf"
        )
        self.assertEqual(result["tag"], "display_notification")
        self.assertEqual(result["params"]["type"], "success")

    def test_action_upload_file_returns_warning_notification_on_failure(self):
        self.env["dropbox.dashboard"].create({
            "dropbox_client_id": "client-id",
            "dropbox_client_secret": "client-secret",
            "dropbox_refresh_token": "refresh-token",
        })
        wizard = self.env["dropbox.upload"].create({
            "file_name": "report.pdf",
            "file": base64.b64encode(b"report content").decode(),
        })

        with patch(
            "odoo.addons.dropbox_integration.wizard.dropbox_upload.dropbox.Dropbox",
            side_effect=dropbox.exceptions.DropboxException("upload failed"),
        ):
            result = wizard.action_upload_file()

        self.assertEqual(result["tag"], "display_notification")
        self.assertEqual(result["params"]["type"], "warning")
        self.assertIn("upload failed", result["params"]["message"])

    def test_action_upload_file_uploads_direct_binary(self):
        config = self.env["ir.config_parameter"].sudo()
        config.set_str("dropbox_integration.folder_id", "/odoo")
        self.env["dropbox.dashboard"].create({
            "dropbox_client_id": "client-id",
            "dropbox_client_secret": "client-secret",
            "dropbox_refresh_token": "refresh-token",
        })
        wizard = self.env["dropbox.upload"].create({
            "file_name": "direct.txt",
            "file": base64.b64encode(b"direct file content").decode(),
        })

        with patch(
            "odoo.addons.dropbox_integration.wizard.dropbox_upload.dropbox.Dropbox"
        ) as dropbox_mock:
            result = wizard.action_upload_file()

        dropbox_mock.return_value.files_upload.assert_called_once_with(
            b"direct file content", "/odoo/direct.txt"
        )
        self.assertEqual(result["tag"], "display_notification")
        self.assertEqual(result["params"]["type"], "success")

    def test_action_upload_file_scope_error_formatting(self):
        self.env["dropbox.dashboard"].create({
            "dropbox_client_id": "client-id",
            "dropbox_client_secret": "client-secret",
            "dropbox_refresh_token": "refresh-token",
        })
        wizard = self.env["dropbox.upload"].create({
            "file_name": "direct.txt",
            "file": base64.b64encode(b"direct file content").decode(),
        })

        with patch(
            "odoo.addons.dropbox_integration.wizard.dropbox_upload.dropbox.Dropbox"
        ) as dropbox_mock:
            dropbox_mock.return_value.files_upload.side_effect = (
                dropbox.exceptions.DropboxException(
                    "does not have the required scope 'files.content.write'"
                )
            )
            result = wizard.action_upload_file()

        self.assertEqual(result["tag"], "display_notification")
        self.assertEqual(result["params"]["type"], "warning")
        self.assertIn("files.content.write", result["params"]["message"])
        self.assertIn("Permissions tab", result["params"]["message"])

    def test_security_action_upload_file_restricted_from_portal_users(self):
        portal_user = self.env["res.users"].create({
            "name": "Portal User Upload Test",
            "login": "portal_user_upload_test",
            "group_ids": [(6, 0, [self.env.ref("base.group_portal").id])],
        })
        wizard = self.env["dropbox.upload"].create({"file_name": "direct.txt"})
        with self.assertRaises(AccessError):
            wizard.with_user(portal_user).action_upload_file()
