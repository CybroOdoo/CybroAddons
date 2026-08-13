# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestEmployeePurchaseRequisition(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Employee Contact'})
        cls.product = cls.env['product.product'].create({
            'name': 'Requisition Product',
            'type': 'consu',
        })
        
        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        if not cls.warehouse:
            cls.warehouse = cls.env['stock.warehouse'].create({
                'name': 'Test Warehouse',
                'code': 'TWH',
            })
            
        cls.source_loc = cls.env['stock.location'].create({
            'name': 'Source Loc',
            'usage': 'internal',
            'location_id': cls.warehouse.view_location_id.id,
        })
        cls.dest_loc = cls.env['stock.location'].create({
            'name': 'Dest Loc',
            'usage': 'internal',
            'location_id': cls.warehouse.view_location_id.id,
        })
        
        if not cls.source_loc.warehouse_id:
            cls.source_loc.warehouse_id = cls.warehouse.id
        if not cls.dest_loc.warehouse_id:
            cls.dest_loc.warehouse_id = cls.warehouse.id

        cls.dept = cls.env['hr.department'].create({
            'name': 'Test Department',
            'department_location_id': cls.source_loc.id,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'department_id': cls.dept.id,
            'employee_location_id': cls.dest_loc.id,
            'work_contact_id': cls.partner.id,
        })

    def test_requisition_lifecycle(self):
        """Test the lifecycle and actions of an employee purchase requisition."""
        seq = self.env['ir.sequence'].search([('code', '=', 'employee.purchase.requisition')])
        if not seq:
            self.env['ir.sequence'].create({
                'name': 'Employee Requisition Sequence',
                'code': 'employee.purchase.requisition',
                'prefix': 'EPR',
                'padding': 5,
            })

        requisition = self.env['employee.purchase.requisition'].create({
            'name': 'REQ-TEST-UNIQUE-01',
            'employee_id': self.employee.id,
            'user_id': self.env.user.id,
            'requisition_order_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 10,
                    'requisition_type': 'purchase_order',
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 5,
                    'requisition_type': 'internal_transfer',
                })
            ]
        })
        
        self.assertEqual(requisition.state, 'new')
        self.assertTrue(requisition.has_internal)
        
        # Confirm Requisition
        requisition.action_confirm_requisition()
        self.assertEqual(requisition.state, 'waiting_department_approval')
        
        # Approve department
        requisition.action_department_approval()
        self.assertEqual(requisition.state, 'waiting_head_approval')
        
        # Approve head
        requisition.action_head_approval()
        self.assertEqual(requisition.state, 'approved')
        
        # Create Purchase Order & Transfer
        requisition.action_create_purchase_order()
        self.assertEqual(requisition.state, 'purchase_order_created')
        self.assertEqual(requisition.purchase_count, 1)
        self.assertEqual(requisition.internal_transfer_count, 1)
        
        # Receive Requisition
        requisition.action_receive()
        self.assertEqual(requisition.state, 'received')
        
        # Test navigation actions
        po_action = requisition.get_purchase_order()
        self.assertEqual(po_action['res_model'], 'purchase.order')
        
        int_action = requisition.get_internal_transfer()
        self.assertEqual(int_action['res_model'], 'stock.picking')
        
        # Test cancellation from new/waiting department approval
        req_cancel = self.env['employee.purchase.requisition'].create({
            'name': 'REQ-CANCEL-UNIQUE-02',
            'employee_id': self.employee.id,
            'user_id': self.env.user.id,
            'requisition_order_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'requisition_type': 'purchase_order',
            })]
        })
        req_cancel.action_confirm_requisition()
        req_cancel.action_department_cancel()
        self.assertEqual(req_cancel.state, 'cancelled')
