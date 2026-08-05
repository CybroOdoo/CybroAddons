# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
from odoo.tests import TransactionCase, tagged

@tagged('-at_install', 'post_install')
class TestMaintenanceWork(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up test data
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        
        cls.equipment = cls.env['maintenance.equipment'].create({
            'name': 'Test Equipment',
        })
        
        # References for stages
        cls.stage_1 = cls.env.ref('maintenance.stage_1', raise_if_not_found=False)
        cls.stage_3 = cls.env.ref('maintenance.stage_3', raise_if_not_found=False)
        cls.stage_0 = cls.env.ref('maintenance.stage_0', raise_if_not_found=False)

        cls.maintenance_request = cls.env['maintenance.request'].create({
            'name': 'Test Maintenance Request',
            'equipment_id': cls.equipment.id,
            'stage_id': cls.stage_1.id if cls.stage_1 else False,
        })
        
        cls.material_request = cls.env['material.request'].create({
            'equipment_id': cls.equipment.id,
            'product_qty': 5,
            'maintenance_request_id': cls.maintenance_request.id,
        })

    def test_material_request_flow(self):
        """Test material request operations"""
        self.assertEqual(self.material_request.state, 'in_progress', "Initial state should be in_progress")
        
        self.material_request.action_receive()
        self.assertEqual(self.material_request.state, 'received', "State should be received after action_receive")
        self.assertTrue(self.material_request.is_product_received, "is_product_received should be True")
        
        self.material_request.action_cancel()
        self.assertEqual(self.material_request.state, 'cancel', "State should be cancel after action_cancel")

    def test_maintenance_request_actions(self):
        """Test actions on maintenance request"""
        action = self.maintenance_request.action_main_create_work_order()
        self.assertTrue(self.maintenance_request.is_create_work_order)
        self.assertEqual(action.get('res_model'), 'maintenance.work')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        
        action2 = self.maintenance_request.action_create_material_request()
        self.assertTrue(self.maintenance_request.is_material_request)
        self.assertFalse(self.maintenance_request.is_create_work_order)
        self.assertEqual(action2.get('res_model'), 'material.request')
        self.assertEqual(action2.get('type'), 'ir.actions.act_window')

    def test_maintenance_work_flow(self):
        """Test maintenance work operations"""
        work_order = self.env['maintenance.work'].create({
            'maintenance_request_id': self.maintenance_request.id,
            'equipment_id': self.equipment.id,
            'partner_id': self.partner.id,
            'duration': 2.0,
        })
        
        self.assertEqual(work_order.state, 'ready', "Initial state should be ready")
        
        work_order.action_confirm()
        self.assertEqual(work_order.state, 'progress', "State should be progress after confirm")
        
        work_order.action_complete_order()
        self.assertEqual(work_order.state, 'done', "State should be done after complete")
        if self.stage_3:
            self.assertEqual(self.maintenance_request.stage_id.id, self.stage_3.id, "Stage should be updated to stage_3")
        
        # Test Invoice Creation
        invoice_action = work_order.action_create_invoice()
        self.assertEqual(work_order.state, 'invoice', "State should be invoice")
        self.assertEqual(invoice_action.get('res_model'), 'account.move', "Should return account.move action")
        
        self.assertEqual(work_order.invoice_count, 1, "Invoice count should be 1")
        
        details = work_order.invoice_details()
        self.assertEqual(details.get('res_model'), 'account.move')
        
        work_order.action_cancel()
        self.assertEqual(work_order.state, 'cancelled', "State should be cancelled")
