# -*- coding: utf-8 -*-
###############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged

GROUP = 'employee_purchase_requisition.'


@tagged('post_install', '-at_install')
class TestPurchaseRequisition(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.requester = new_test_user(
            cls.env, login='epr_requester', groups='base.group_user,' + GROUP + 'employee_requisition_user')
        cls.manager = new_test_user(
            cls.env, login='epr_manager',
            groups='base.group_user,stock.group_stock_user,' + GROUP + 'employee_requisition_manager')
        cls.head = new_test_user(
            cls.env, login='epr_head',
            groups='base.group_user,stock.group_stock_user,' + GROUP + 'employee_requisition_head')
        cls.plain = new_test_user(cls.env, login='epr_plain', groups='base.group_user')
        cls.vendor = cls.env['res.partner'].create({'name': 'EPR Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'EPR Chair', 'is_storable': True,
            'seller_ids': [(0, 0, {'partner_id': cls.vendor.id, 'price': 10})]})
        cls.product_2 = cls.env['product.product'].create({'name': 'EPR Desk', 'is_storable': True})
        cls.employee = cls.env['hr.employee'].create({'name': 'EPR Employee'})

    def _requisition(self, lines=None):
        lines = lines if lines is not None else [{'product_id': self.product.id, 'quantity': 2,
                           'requisition_type': 'purchase_order', 'partner_id': self.vendor.id}]
        return self.env['employee.purchase.requisition'].with_user(self.requester).create({
            'employee_id': self.employee.id, 'user_id': self.manager.id,
            'requisition_order_ids': [(0, 0, line) for line in lines]})

    def _approved(self, lines=None):
        requisition = self._requisition(lines)
        requisition.with_user(self.requester).action_confirm_requisition()
        requisition.with_user(self.manager).action_department_approval()
        requisition.with_user(self.head).action_head_approval()
        return requisition

    def test_full_flow_creates_purchase_order_and_transfer(self):
        requisition = self._approved([
            {'product_id': self.product.id, 'quantity': 2, 'requisition_type': 'purchase_order',
             'partner_id': self.vendor.id},
            {'product_id': self.product_2.id, 'quantity': 3, 'requisition_type': 'internal_transfer'},
        ])
        self.assertTrue(requisition.name.startswith('EPR'))
        self.assertEqual(requisition.state, 'approved')
        self.assertEqual(requisition.manager_id, self.manager)
        self.assertEqual(requisition.requisition_head_id, self.head)
        requisition.with_user(self.manager).action_create_purchase_order()
        self.assertEqual(requisition.state, 'purchase_order_created')
        self.assertEqual(requisition.purchase_count, 1)
        self.assertEqual(requisition.internal_transfer_count, 1)
        order = self.env['purchase.order'].search([('requisition_order', '=', requisition.name)])
        self.assertEqual(order.partner_id, self.vendor)
        self.assertEqual(order.order_line.product_qty, 2)
        picking = self.env['stock.picking'].search([('requisition_order', '=', requisition.name)])
        self.assertEqual(picking.move_ids.product_id, self.product_2)
        self.assertEqual(picking.move_ids.product_uom_qty, 3)
        self.assertEqual(picking.move_ids.uom_id, self.product_2.uom_id)
        self.assertEqual(requisition.get_purchase_order()['res_model'], 'purchase.order')
        self.assertEqual(requisition.get_internal_transfer()['res_model'], 'stock.picking')
        # As the manager: an admin first gets the company report-layout wizard.
        self.assertEqual(order.with_user(self.manager).action_print_requisition_report()['type'],
                         'ir.actions.report')
        requisition.with_user(self.manager).action_receive()
        self.assertEqual(requisition.state, 'received')
        self.assertTrue(requisition.receive_date)

    def test_rejections(self):
        requisition = self._requisition()
        requisition.with_user(self.requester).action_confirm_requisition()
        requisition.with_user(self.manager).action_department_cancel()
        self.assertEqual(requisition.state, 'cancelled')
        self.assertEqual(requisition.rejected_user_id, self.manager)
        requisition = self._requisition()
        requisition.with_user(self.requester).action_confirm_requisition()
        requisition.with_user(self.manager).action_department_approval()
        requisition.with_user(self.head).action_head_cancel()
        self.assertEqual(requisition.state, 'cancelled')
        self.assertEqual(requisition.rejected_user_id, self.head)

    def test_buttons_check_the_state(self):
        """Each button only works in the state that shows it."""
        requisition = self._requisition()
        with self.assertRaises(UserError):
            requisition.with_user(self.head).action_head_approval()
        with self.assertRaises(UserError):
            requisition.with_user(self.manager).action_create_purchase_order()
        with self.assertRaises(UserError):
            requisition.with_user(self.manager).action_receive()
        with self.assertRaises(UserError):
            requisition.with_user(self.manager).action_department_approval()
        self.assertEqual(requisition.state, 'new')
        self.assertEqual(requisition.purchase_count, 0)

    def test_state_cannot_be_written_directly(self):
        requisition = self._requisition()
        with self.assertRaises(UserError):
            requisition.with_user(self.requester).write({'state': 'approved'})
        with self.assertRaises(UserError):
            self.env['employee.purchase.requisition'].with_user(self.requester).create({
                'employee_id': self.employee.id, 'user_id': self.manager.id, 'state': 'approved'})
        self.assertEqual(requisition.state, 'new')

    def test_role_checks(self):
        requisition = self._requisition()
        with self.assertRaises(UserError):
            self._requisition([]).with_user(self.requester).action_confirm_requisition()
        requisition.with_user(self.requester).action_confirm_requisition()
        with self.assertRaises(UserError):
            requisition.with_user(self.head).action_department_approval()
        with self.assertRaises(UserError):
            requisition.with_user(self.head).action_department_cancel()
        requisition.with_user(self.manager).action_department_approval()
        with self.assertRaises(UserError):
            requisition.with_user(self.manager).action_head_approval()
        requisition.sudo().manager_id = self.head
        with self.assertRaises(UserError):
            requisition.with_user(self.head).action_head_approval()
        requisition.sudo().manager_id = self.manager
        requisition.with_user(self.head).action_head_approval()
        with self.assertRaises(UserError):
            requisition.with_user(self.requester).action_create_purchase_order()
        requisition.with_user(self.manager).action_create_purchase_order()
        with self.assertRaises(UserError):
            requisition.with_user(self.requester).action_receive()

    def test_department_approval_needs_vendor(self):
        requisition = self._requisition([{'product_id': self.product_2.id, 'requisition_type': 'purchase_order'}])
        requisition.with_user(self.requester).action_confirm_requisition()
        with self.assertRaises(ValidationError):
            requisition.with_user(self.manager).action_department_approval()

    def test_lines_locked_after_approval(self):
        requisition = self._requisition()
        line = requisition.requisition_order_ids
        line.with_user(self.requester).write({'quantity': 5})
        self.assertEqual(line.quantity, 5)
        requisition = self._approved()
        line = requisition.requisition_order_ids
        with self.assertRaises(UserError):
            line.with_user(self.plain).write({'quantity': 99})
        with self.assertRaises(UserError):
            self.env['requisition.order'].with_user(self.plain).create({
                'requisition_product_id': requisition.id, 'product_id': self.product.id})
        with self.assertRaises(UserError):
            line.with_user(self.plain).unlink()
        draft = self._requisition()
        with self.assertRaises(UserError):
            draft.requisition_order_ids.with_user(self.requester).write({'requisition_product_id': requisition.id})
        self.assertEqual(line.quantity, 2)

    def test_requester_opens_own_requisition(self):
        """The form's smart-button counts must not need purchase or stock rights."""
        requisition = self._requisition().with_user(self.requester)
        self.env.invalidate_all()
        self.assertEqual(requisition.purchase_count, 0)
        self.assertEqual(requisition.internal_transfer_count, 0)

    def test_requester_deletes_own_requisition(self):
        """Deleting works for a requester who has no purchase rights."""
        requisition = self._requisition()
        requisition.with_user(self.requester).unlink()
        self.assertFalse(requisition.exists())

    def test_delete_cancels_draft_po_and_keeps_confirmed(self):
        requisition = self._approved()
        requisition.with_user(self.manager).action_create_purchase_order()
        order = self.env['purchase.order'].search([('requisition_order', '=', requisition.name)])
        order.write({'state': 'purchase'})
        with self.assertRaises(UserError):
            requisition.with_user(self.head).unlink()
        requisition = self._approved()
        requisition.with_user(self.manager).action_create_purchase_order()
        order = self.env['purchase.order'].search([('requisition_order', '=', requisition.name)])
        requisition.with_user(self.head).unlink()
        self.assertEqual(order.state, 'cancel')

    def test_description_for_two_requisitions_at_once(self):
        other = self.env['hr.employee'].create({'name': 'EPR Employee 2'})
        requisitions = self.env['employee.purchase.requisition'].create([
            {'employee_id': employee.id, 'user_id': self.manager.id,
             'requisition_order_ids': [(0, 0, {'product_id': self.product.id})]}
            for employee in (self.employee, other)])
        self.assertTrue(all(requisitions.requisition_order_ids.mapped('description')))

    def test_print_and_unlinked_purchase_order(self):
        requisition = self._requisition()
        self.assertEqual(requisition.action_print_report()['type'], 'ir.actions.report')
        order = self.env['purchase.order'].create({'partner_id': self.vendor.id})
        with self.assertRaises(UserError):
            order.action_print_requisition_report()

    def test_vendor_onchange(self):
        line = self.env['requisition.order'].new({'product_id': self.product.id})
        result = line._onchange_requisition_type()
        self.assertEqual(result['domain']['partner_id'], [('id', 'in', [self.vendor.id])])
