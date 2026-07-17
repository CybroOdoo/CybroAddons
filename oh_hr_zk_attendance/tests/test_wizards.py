# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestZkWizardBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env.ref("hr.employee_admin", raise_if_not_found=False) or cls.env["hr.employee"].search([], limit=1)
        cls.partner = cls.env.ref("base.partner_admin")
        cls.device = cls.env["biometric.device.details"].create({
            "name": "Wizard Device",
            "device_ip": "192.168.1.20",
            "port_number": 4370,
            "address_id": cls.partner.id,
        })

    def setUp(self):
        super().setUp()
        self._sharepoint_upload_patcher = patch(
            "odoo.addons.odoo_sharepoint_connector.models.ir_attachment.IrAttachment._upload_to_sharepoint_if_needed",
            autospec=True,
        )
        self._sharepoint_upload_patcher.start()
        self.addCleanup(self._sharepoint_upload_patcher.stop)


class TestEmployeeBiometric(TestZkWizardBase):
    def test_compute_is_biometric_user(self):
        self.employee.write({"device_id_num": "BIO-1", "device_id": self.device.id})
        wizard = self.env["employee.biometric"].create({
            "employee_id": self.employee.id,
        })

        wizard._compute_is_biometric_user()
        self.assertTrue(wizard.is_biometric_user)

        self.employee.write({"device_id_num": False, "device_id": False})
        wizard._compute_is_biometric_user()
        self.assertFalse(wizard.is_biometric_user)

    def test_action_confirm_biometric_management_creates_user(self):
        self.employee.write({"device_id_num": False, "device_id": False})
        wizard = self.env["employee.biometric"].create({
            "employee_id": self.employee.id,
            "biometric_device_id": self.device.id,
        })

        with patch.object(type(self.device), "set_user", autospec=True) as set_user:
            wizard.action_confirm_biometric_management()

        self.assertEqual(self.employee.device_id, self.device)
        set_user.assert_called_once_with(self.device, employee_id=self.employee.id)

    def test_action_confirm_biometric_management_updates_existing_user(self):
        self.employee.write({"device_id_num": "BIO-2", "device_id": self.device.id})
        wizard = self.env["employee.biometric"].create({
            "employee_id": self.employee.id,
            "handle_update_delete": "update_user",
        })
        wizard._compute_is_biometric_user()

        with patch.object(type(self.device), "update_user", autospec=True) as update_user:
            wizard.action_confirm_biometric_management()

        update_user.assert_called_once_with(self.device, employee_id=self.employee.id)

    def test_action_confirm_biometric_management_deletes_existing_user(self):
        self.employee.write({"device_id_num": "BIO-3", "device_id": self.device.id})
        wizard = self.env["employee.biometric"].create({
            "employee_id": self.employee.id,
            "handle_update_delete": "delete_user",
        })
        wizard._compute_is_biometric_user()

        with patch.object(type(self.device), "delete_user", autospec=True) as delete_user:
            wizard.action_confirm_biometric_management()

        delete_user.assert_called_once_with(
            self.device,
            employee_id=self.employee.id,
            employee_user_selection=None,
        )


class TestZkUserManagement(TestZkWizardBase):
    def test_compute_employee_ids_for_create_user(self):
        self.employee.write({"device_id": False, "device_id_num": False})
        wizard = self.env["zk.user.management"].with_context(active_id=self.device.id).create({
            "manage_users": "create_user",
        })

        wizard._compute_employee_ids()
        self.assertIn(self.employee, wizard.employee_ids)

    def test_compute_employee_ids_for_update_delete(self):
        self.employee.write({"device_id": self.device.id, "device_id_num": "BIO-4"})
        wizard = self.env["zk.user.management"].with_context(active_id=self.device.id).create({
            "manage_users": "update_user",
        })

        wizard._compute_employee_ids()
        self.assertIn(self.employee, wizard.employee_ids)

    def test_action_confirm_user_management_get_users_returns_action(self):
        wizard = self.env["zk.user.management"].with_context(active_id=self.device.id).create({
            "manage_users": "get_users",
        })

        with patch.object(type(self.device), "get_all_users", autospec=True) as get_all_users:
            action = wizard.action_confirm_user_management()

        get_all_users.assert_called_once_with(self.device)
        self.assertEqual(action["res_model"], "hr.employee")
        self.assertEqual(action["domain"], [("device_id", "=", self.device.id)])

    def test_action_confirm_user_management_create_user(self):
        wizard = self.env["zk.user.management"].with_context(active_id=self.device.id).create({
            "manage_users": "create_user",
            "employee_id": self.employee.id,
        })

        with patch.object(type(self.device), "set_user", autospec=True) as set_user:
            wizard.action_confirm_user_management()

        set_user.assert_called_once_with(self.device, employee_id=self.employee.id)

    def test_action_confirm_user_management_update_user(self):
        wizard = self.env["zk.user.management"].with_context(active_id=self.device.id).create({
            "manage_users": "update_user",
            "employee_id": self.employee.id,
        })

        with patch.object(type(self.device), "update_user", autospec=True) as update_user:
            wizard.action_confirm_user_management()

        update_user.assert_called_once_with(self.device, employee_id=self.employee.id)

    def test_action_confirm_user_management_delete_user(self):
        wizard = self.env["zk.user.management"].with_context(active_id=self.device.id).create({
            "manage_users": "delete_user",
            "employee_id": self.employee.id,
            "delete_user_selection": "device_only",
        })

        with patch.object(type(self.device), "delete_user", autospec=True) as delete_user:
            wizard.action_confirm_user_management()

        delete_user.assert_called_once_with(
            self.device,
            employee_id=self.employee.id,
            employee_user_selection="device_only",
        )
