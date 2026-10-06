# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

###############################################################################
from odoo.tests.common import TransactionCase
from odoo import Command

class TestEmployeePurchaseRequisition(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_po = cls.env['product.product'].create({
            'name': 'Test Product PO',
            'type': 'consu',
        })
        cls.product_transfer = cls.env['product.product'].create({
            'name': 'Test Product Transfer',
            'type': 'consu',
        })
        cls.department = cls.env['hr.department'].create({
            'name': 'Test Dept',
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'department_id': cls.department.id,
        })
        
        cls.requisition = cls.env['employee.purchase.requisition'].create({
            'employee_id': cls.employee.id,
            'user_id': cls.env.user.id,
            'requisition_order_ids': [
                Command.create({
                    'product_id': cls.product_po.id,
                    'quantity': 5,
                    'requisition_type': 'purchase_order',
                }),
                Command.create({
                    'product_id': cls.product_transfer.id,
                    'quantity': 2,
                    'requisition_type': 'internal_transfer',
                })
            ]
        })

    def test_compute_has_internal(self):
        """Test compute has_internal flag."""
        self.requisition._compute_has_internal()
        self.assertTrue(self.requisition.has_internal)

    def test_requisition_lifecycle(self):
        """Test the approval and creation lifecycle."""
        # 1. Confirm
        self.requisition.action_confirm_requisition()
        self.assertEqual(self.requisition.state, 'waiting_department_approval')
        
        # 2. Dept Approval
        self.requisition.action_department_approval()
        self.assertEqual(self.requisition.state, 'waiting_head_approval')
        
        # 3. Head Approval
        self.requisition.action_head_approval()
        self.assertEqual(self.requisition.state, 'approved')
        
        # 4. Create PO
        self.requisition.action_create_purchase_order()
        self.assertEqual(self.requisition.state, 'purchase_order_created')
        self.assertEqual(self.requisition.purchase_count, 1)
        self.assertEqual(self.requisition.internal_transfer_count, 1)
        
        # 5. Receive
        self.requisition.action_receive()
        self.assertEqual(self.requisition.state, 'received')

    def test_cancellation_routes(self):
        """Test cancellation from department and head."""
        req1 = self.env['employee.purchase.requisition'].create({
            'employee_id': self.employee.id,
            'user_id': self.env.user.id,
            'requisition_order_ids': [Command.create({
                'product_id': self.product_po.id,
                'quantity': 1,
                'requisition_type': 'purchase_order',
            })]
        })
        req1.action_confirm_requisition()
        req1.action_department_cancel()
        self.assertEqual(req1.state, 'cancelled')
        
        req2 = self.env['employee.purchase.requisition'].create({
            'employee_id': self.employee.id,
            'user_id': self.env.user.id,
            'requisition_order_ids': [Command.create({
                'product_id': self.product_po.id,
                'quantity': 1,
                'requisition_type': 'purchase_order',
            })]
        })
        req2.action_confirm_requisition()
        req2.action_department_approval()
        req2.action_head_cancel()
        self.assertEqual(req2.state, 'cancelled')

    def test_smart_buttons(self):
        """Test action dictionary returns from smart buttons."""
        action_po = self.requisition.get_purchase_order()
        self.assertEqual(action_po['res_model'], 'purchase.order')
        
        action_pick = self.requisition.get_internal_transfer()
        self.assertEqual(action_pick['res_model'], 'stock.picking')

    def test_print_report(self):
        """Test print report action."""
        action_report = self.requisition.action_print_report()
        self.assertIn(action_report.get('type'), ('ir.actions.report', 'ir.actions.act_window'))
