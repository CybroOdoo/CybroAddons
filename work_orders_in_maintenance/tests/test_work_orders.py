# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)
#    (https://www.gnu.org/licenses/lgpl-3.0-standalone.html).
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWorkOrders(TransactionCase):
    """Test the work order, material request and invoice flows."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.equipment = cls.env["maintenance.equipment"].create(
            {"name": "Test Equipment"}
        )
        cls.stage_new = cls.env.ref("maintenance.stage_0")
        cls.stage_progress = cls.env.ref("maintenance.stage_1")
        cls.stage_repaired = cls.env.ref("maintenance.stage_3")
        cls.request = cls.env["maintenance.request"].create(
            {
                "name": "Broken Machine",
                "equipment_id": cls.equipment.id,
                "stage_id": cls.stage_new.id,
            }
        )
        cls.work = cls.env["maintenance.work"].create(
            {
                "maintenance_request_id": cls.request.id,
                "equipment_id": cls.equipment.id,
                "partner_id": cls.partner.id,
                "duration": 2.0,
            }
        )
        cls.material = cls.env["material.request"].create(
            {
                "maintenance_request_id": cls.request.id,
                "equipment_id": cls.equipment.id,
                "product_qty": 3.0,
            }
        )

    def test_sequences(self):
        """Work orders and material requests get a sequence reference."""
        self.assertTrue(self.work.name.startswith("WO"))
        self.assertTrue(self.material.name.startswith("MR"))
        named = self.env["maintenance.work"].create({"name": "Custom"})
        self.assertEqual(named.name, "Custom")

    def test_work_order_flow(self):
        """The work order moves through its states."""
        self.assertEqual(self.work.state, "ready")
        self.work.action_confirm()
        self.assertEqual(self.work.state, "progress")
        self.work.action_complete_order()
        self.assertEqual(self.work.state, "done")
        self.assertEqual(self.request.stage_id, self.stage_repaired)

    def test_work_order_cancel(self):
        """A work order can be cancelled."""
        self.work.action_cancel()
        self.assertEqual(self.work.state, "cancelled")

    def test_work_order_invoice(self):
        """Creating the invoice links it to the work order and request."""
        self.assertEqual(self.work.invoice_count, 0)
        action = self.work.action_create_invoice()
        invoice = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(self.work.state, "invoice")
        self.assertEqual(self.work.invoice_id, invoice)
        self.assertEqual(invoice.maintenance_request_id, self.request)
        self.assertEqual(invoice.partner_id, self.partner)
        self.work.invalidate_recordset(["invoice_count"])
        self.assertEqual(self.work.invoice_count, 1)
        details = self.work.invoice_details()
        self.assertEqual(details["res_model"], "account.move")
        self.assertIn(
            ("maintenance_request_id", "=", self.request.id), details["domain"]
        )

    def test_invoice_count_without_request(self):
        """A work order without request has no invoices."""
        work = self.env["maintenance.work"].create({})
        self.assertEqual(work.invoice_count, 0)

    def test_material_request_flow(self):
        """Material requests can be received or cancelled."""
        self.assertEqual(self.material.state, "in_progress")
        self.assertFalse(self.material.is_product_received)
        self.material.action_receive()
        self.assertEqual(self.material.state, "received")
        self.assertTrue(self.material.is_product_received)
        self.material.action_cancel()
        self.assertEqual(self.material.state, "cancel")
        self.assertFalse(self.material.is_product_received)

    def test_request_counts_and_actions(self):
        """The maintenance request counts and opens its records."""
        self.assertEqual(self.request.work_order_count, 1)
        self.assertEqual(self.request.material_request_count, 1)
        action = self.request.action_view_work_orders()
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["res_id"], self.work.id)
        action = self.request.action_view_material_requests()
        self.assertEqual(action["res_id"], self.material.id)
        self.env["maintenance.work"].create(
            {"maintenance_request_id": self.request.id}
        )
        self.env["material.request"].create(
            {"maintenance_request_id": self.request.id}
        )
        self.assertEqual(self.request.work_order_count, 2)
        action = self.request.action_view_work_orders()
        self.assertEqual(action["view_mode"], "list,form")
        action = self.request.action_view_material_requests()
        self.assertEqual(action["view_mode"], "list,form")

    def test_create_work_order_availability(self):
        """Work orders can be created once the material is received."""
        self.request.stage_id = self.stage_progress
        self.assertTrue(self.request.is_material_work_order)
        self.assertFalse(self.request.is_create_work_order)
        self.material.action_receive()
        self.assertTrue(self.request.is_create_work_order)
        self.request.stage_id = self.stage_repaired
        self.assertFalse(self.request.is_create_work_order)
        self.assertFalse(self.request.is_material_work_order)

    def test_main_create_work_order(self):
        """The work order action moves the request in progress."""
        action = self.request.action_main_create_work_order()
        self.assertEqual(self.request.stage_id, self.stage_progress)
        self.assertEqual(action["res_model"], "maintenance.work")
        self.assertEqual(action["target"], "new")
        self.assertEqual(
            action["context"]["default_maintenance_request_id"], self.request.id
        )

    def test_create_material_request_action(self):
        """The material request action flags the request."""
        self.assertFalse(self.request.is_material_request)
        action = self.request.action_create_material_request()
        self.assertTrue(self.request.is_material_request)
        self.assertEqual(action["res_model"], "material.request")
        self.assertEqual(action["target"], "new")
