# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Akhil ( odoo@cybrosys.com )
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import base64
from unittest.mock import Mock, patch
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.addons.onedrive_integration_odoo.models.onedrive_dashboard import OneDriveDashboard


@tagged("post_install", "-at_install")
class TestOneDriveIntegration(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env["ir.config_parameter"].sudo()
        cls.config.set_param("onedrive_integration_odoo.onedrive_folder", "Shared")

    def test_action_synchronize_onedrive_returns_file_mapping(self):
        dashboard = self.env["onedrive.dashboard"].create({
            "onedrive_access_token": "access-token",
            "onedrive_refresh_token": "refresh-token",
            "token_expiry_date": "2099-01-01 00:00:00",
        })
        response = Mock()
        response.content = b'{"value": []}'
        response.json.return_value = {
            "value": [
                {
                    "@microsoft.graph.downloadUrl": "https://example.com/report",
                    "name": "report.pdf",
                },
                {
                    "id": "folder-id",
                    "name": "Documents",
                },
            ]
        }

        with patch(
            "odoo.addons.onedrive_integration_odoo.models.onedrive_dashboard.requests.get",
            return_value=response,
        ) as get_mock:
            result = dashboard.action_synchronize_onedrive()

        get_mock.assert_called_once()
        self.assertEqual(result, {"report.pdf": "https://example.com/report"})

    def test_action_synchronize_onedrive_refreshes_expired_token(self):
        dashboard = self.env["onedrive.dashboard"].create({
            "onedrive_access_token": "access-token",
            "onedrive_refresh_token": "refresh-token",
            "token_expiry_date": "2000-01-01 00:00:00",
        })
        response = Mock()
        response.content = b'{"value": []}'
        response.json.return_value = {"value": []}

        with patch.object(
            OneDriveDashboard,
            "generate_onedrive_refresh_token",
            autospec=True,
        ) as refresh_mock, patch(
            "odoo.addons.onedrive_integration_odoo.models.onedrive_dashboard.requests.get",
            return_value=response,
        ):
            dashboard.action_synchronize_onedrive()

        refresh_mock.assert_called_once_with(dashboard)

    def test_action_upload_file_returns_success_notification(self):
        self.env["onedrive.dashboard"].create({
            "onedrive_access_token": "access-token",
            "onedrive_refresh_token": "refresh-token",
            "token_expiry_date": "2099-01-01 00:00:00",
        })
        wizard = self.env["upload.file"].create({
            "file": base64.b64encode(b"hello onedrive"),
            "file_name": "hello.txt",
        })
        response = Mock(status_code=201, text="created")

        with patch(
            "odoo.addons.onedrive_integration_odoo.wizard.upload_file.requests.put",
            return_value=response,
        ) as put_mock:
            action = wizard.action_upload_file()

        put_mock.assert_called_once()
        _, kwargs = put_mock.call_args
        self.assertEqual(kwargs["data"], b"hello onedrive")
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["type"], "success")

    def test_action_upload_file_requires_binary_file(self):
        wizard = self.env["upload.file"].create({
            "file_name": "missing.txt",
        })

        with self.assertRaises(UserError):
            wizard.action_upload_file()
