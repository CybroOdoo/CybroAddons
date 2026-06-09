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

import base64
from unittest.mock import mock_open, patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDropboxUpload(TransactionCase):

    def test_action_upload_file_uploads_attachment_to_configured_folder(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "dropbox_integration.folder_id", "/odoo"
        )
        self.env["dropbox.dashboard"].create({
            "dropbox_client_id": "client-id",
            "dropbox_client_secret": "client-secret",
            "dropbox_refresh_token": "refresh-token",
        })
        wizard = self.env["dropbox.upload"].create({"file_name": "report.pdf"})
        self.env["ir.attachment"].create({
            "name": "report.pdf",
            "type": "binary",
            "datas": base64.b64encode(b"report content").decode(),
            "res_model": "dropbox.upload",
            "res_id": wizard.id,
        })
        open_mock = mock_open(read_data=b"report content")

        with patch(
            "odoo.addons.dropbox_integration.wizard.dropbox_upload.dropbox.Dropbox"
        ) as dropbox_mock, patch("builtins.open", open_mock):
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
        wizard = self.env["dropbox.upload"].create({"file_name": "report.pdf"})

        with patch(
            "odoo.addons.dropbox_integration.wizard.dropbox_upload.dropbox.Dropbox",
            side_effect=RuntimeError("upload failed"),
        ):
            result = wizard.action_upload_file()

        self.assertEqual(result["tag"], "display_notification")
        self.assertEqual(result["params"]["type"], "warning")
        self.assertIn("upload failed", result["params"]["message"])
