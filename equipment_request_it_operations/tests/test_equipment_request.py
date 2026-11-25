# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arshad Ali Pottengal (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestEquipmentRequest(common.TransactionCase):
    """Test suite for the equipment.request model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Groups
        cls.group_dept_manager = cls.env.ref(
            'equipment_request_it_operations'
            '.equipment_request_it_operations_group_department_manager'
        )
        cls.group_hr_officer = cls.env.ref(
            'equipment_request_it_operations'
            '.equipment_request_it_operations_group_hr_officer'
        )
        cls.group_stock_manager = cls.env.ref(
            'equipment_request_it_operations'
            '.equipment_request_it_operations_group_stock_manager'
        )

        # Department / Job
        cls.department = cls.env['hr.department'].create(
            {'name': 'IT Dept Test'})
        cls.job = cls.env['hr.job'].create({'name': 'Developer Test'})

        # Employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'department_id': cls.department.id,
            'job_id': cls.job.id,
        })

        # Create users first; groups are assigned below through the group's
        # 'user_ids' field
        cls.plain_user = cls.env['res.users'].create({
            'name': 'Plain User',
            'login': 'plain_user_eq_req_test',
        })
        cls.dept_mgr_user = cls.env['res.users'].create({
            'name': 'Dept Manager User',
            'login': 'dept_mgr_eq_req_test',
        })
        cls.hr_officer_user = cls.env['res.users'].create({
            'name': 'HR Officer User',
            'login': 'hr_officer_eq_req_test',
        })
        cls.stock_mgr_user = cls.env['res.users'].create({
            'name': 'Stock Manager User',
            'login': 'stock_mgr_eq_req_test',
        })

        # Assign the module-specific groups
        cls.group_dept_manager.write({'user_ids': [(4, cls.dept_mgr_user.id)]})
        cls.group_hr_officer.write({'user_ids': [(4, cls.hr_officer_user.id)]})
        cls.group_stock_manager.write(
            {'user_ids': [(4, cls.stock_mgr_user.id)]})

        # Stock locations
        cls.src_location = cls.env['stock.location'].create({
            'name': 'Test Source Location',
            'usage': 'internal',
        })
        cls.dest_location = cls.env['stock.location'].create({
            'name': 'Test Destination Location',
            'usage': 'internal',
        })

        # Product for equipment detail
        cls.product = cls.env['product.product'].create({
            'name': 'Test Equipment Product',
            'type': 'consu',
            'lst_price': 150.0,
        })

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _make_request(self, status='draft', **kwargs):
        """Create an equipment.request and optionally force its status."""
        vals = {
            'employee_name_id': self.employee.id,
            'request_for': 'hardware',
        }
        vals.update(kwargs)
        req = self.env['equipment.request'].create(vals)
        if status != 'draft':
            # Force the status to skip chaining through every approval step
            req.write({'status': status})
        return req

    # ------------------------------------------------------------------
    # _compute_name
    # ------------------------------------------------------------------

    def test_compute_name_contains_employee(self):
        """Name should include the employee name."""
        req = self._make_request()
        self.assertIn(self.employee.name, req.name)

    def test_default_created_date_is_today(self):
        """A new request gets today's date as its created date."""
        req = self._make_request()
        self.assertEqual(req.request_create_date, fields.Date.today())

    def test_compute_name_before_save_uses_today(self):
        """An unsaved request uses today's date in its name."""
        req = self.env['equipment.request'].new({
            'request_for': 'software',
            'employee_name_id': self.employee.id,
        })
        self.assertTrue(req.name.endswith(str(fields.Date.today())))

    def test_compute_name_contains_request_for(self):
        """Name should include the request_for value."""
        req = self._make_request()
        self.assertIn('hardware', req.name)

    # ------------------------------------------------------------------
    # _onchange_employee_name_id
    # ------------------------------------------------------------------

    def test_onchange_employee_sets_department(self):
        """Changing employee should populate department and job."""
        req = self.env['equipment.request'].new({
            'request_for': 'software',
            'employee_name_id': self.employee.id,
        })
        req._onchange_employee_name_id()
        self.assertEqual(req.department_name_id, self.department)
        self.assertEqual(req.job_position_id, self.job)

    def test_onchange_employee_no_employee(self):
        """When no employee is set the onchange should not raise."""
        req = self.env['equipment.request'].new({'request_for': 'software'})
        # Should complete without error
        req._onchange_employee_name_id()

    # ------------------------------------------------------------------
    # action_confirm
    # ------------------------------------------------------------------

    def test_action_confirm_draft_to_waiting(self):
        """Confirming a draft request moves it to 'waiting'."""
        req = self._make_request()
        req.action_confirm()
        self.assertEqual(req.status, 'waiting')

    def test_action_confirm_non_draft_raises(self):
        """Confirming a non-draft request raises UserError."""
        req = self._make_request(status='waiting')
        with self.assertRaises(UserError):
            req.action_confirm()

    # ------------------------------------------------------------------
    # action_reject
    # ------------------------------------------------------------------

    def test_action_reject_as_dept_manager(self):
        """Department manager can reject a request."""
        req = self._make_request(status='waiting')
        req.with_user(self.dept_mgr_user).action_reject()
        self.assertEqual(req.status, 'reject')

    def test_action_reject_as_hr_officer(self):
        """HR officer can reject a request."""
        req = self._make_request(status='approval')
        req.with_user(self.hr_officer_user).action_reject()
        self.assertEqual(req.status, 'reject')

    def test_action_reject_as_stock_manager(self):
        """Stock manager can reject a request."""
        req = self._make_request(status='approved')
        req.with_user(self.stock_mgr_user).action_reject()
        self.assertEqual(req.status, 'reject')

    def test_action_reject_plain_user_raises(self):
        """Plain user without any approval group cannot reject."""
        req = self._make_request(status='waiting')
        with self.assertRaises(UserError):
            req.with_user(self.plain_user).action_reject()

    def test_action_reject_already_rejected_raises(self):
        """Rejecting an already-rejected request raises UserError."""
        req = self._make_request(status='reject')
        with self.assertRaises(UserError):
            req.with_user(self.dept_mgr_user).action_reject()

    # ------------------------------------------------------------------
    # action_waiting_approval_dept
    # ------------------------------------------------------------------

    def test_action_waiting_approval_dept_success(self):
        """Department manager can approve a 'waiting' request."""
        req = self._make_request(status='waiting')
        req.with_user(self.dept_mgr_user).action_waiting_approval_dept()
        self.assertEqual(req.status, 'approval')
        self.assertEqual(req.validate_user_id, self.dept_mgr_user)

    def test_action_waiting_approval_dept_wrong_state_raises(self):
        """Dept approval on a non-waiting request raises UserError."""
        req = self._make_request(status='draft')
        with self.assertRaises(UserError):
            req.with_user(self.dept_mgr_user).action_waiting_approval_dept()

    def test_action_waiting_approval_dept_wrong_group_raises(self):
        """Non-dept-manager cannot perform dept approval."""
        req = self._make_request(status='waiting')
        with self.assertRaises(UserError):
            req.with_user(self.plain_user).action_waiting_approval_dept()

    # ------------------------------------------------------------------
    # action_waiting_approval_hr
    # ------------------------------------------------------------------

    def test_action_waiting_approval_hr_success(self):
        """HR officer can approve an 'approval' request."""
        req = self._make_request(status='approval')
        req.with_user(self.hr_officer_user).action_waiting_approval_hr()
        self.assertEqual(req.status, 'approved')
        self.assertEqual(req.hr_user_id, self.hr_officer_user)

    def test_action_waiting_approval_hr_wrong_state_raises(self):
        """HR approval on a non-approval request raises UserError."""
        req = self._make_request(status='waiting')
        with self.assertRaises(UserError):
            req.with_user(self.hr_officer_user).action_waiting_approval_hr()

    def test_action_waiting_approval_hr_wrong_group_raises(self):
        """Non-HR-officer cannot perform HR approval."""
        req = self._make_request(status='approval')
        with self.assertRaises(UserError):
            req.with_user(self.plain_user).action_waiting_approval_hr()

    # ------------------------------------------------------------------
    # action_internal_transfer
    # ------------------------------------------------------------------

    def test_action_internal_transfer_success(self):
        """Stock manager can create a transfer for an approved request."""
        req = self._make_request(
            status='approved',
            source_location_id=self.src_location.id,
            destination_location_id=self.dest_location.id,
        )
        # Add an equipment line
        self.env['equipment.detail'].create({
            'product_id': self.product.id,
            'quantity': 2,
            'equipment_detail_id': req.id,
        })
        req.with_user(self.stock_mgr_user).action_internal_transfer()
        self.assertEqual(req.status, 'assigned')
        self.assertEqual(req.stock_user_id, self.stock_mgr_user)
        self.assertEqual(req.stock_date, fields.Date.today())
        # A confirmed internal picking with one move per line is linked
        picking = req.equipment_internal_ids
        self.assertEqual(len(picking), 1)
        self.assertEqual(picking.picking_type_id.code, 'internal')
        self.assertEqual(picking.location_id, self.src_location)
        self.assertEqual(picking.location_dest_id, self.dest_location)
        self.assertNotEqual(picking.state, 'draft')
        self.assertEqual(picking.move_ids.product_id, self.product)
        self.assertEqual(picking.move_ids.product_uom_qty, 2)
        self.assertEqual(picking.move_ids.product_uom, self.product.uom_id)

    def test_action_internal_transfer_no_picking_type_raises(self):
        """Missing internal operation type for the company raises UserError."""
        req = self._make_request(
            status='approved',
            source_location_id=self.src_location.id,
            destination_location_id=self.dest_location.id,
        )
        picking_type_model = self.env.registry['stock.picking.type']
        with patch.object(picking_type_model, 'search',
                          return_value=self.env['stock.picking.type']):
            with self.assertRaises(UserError):
                req.with_user(self.stock_mgr_user).action_internal_transfer()
        self.assertEqual(req.status, 'approved')

    def test_action_internal_transfer_no_source_raises(self):
        """Missing source location raises UserError."""
        req = self._make_request(
            status='approved',
            destination_location_id=self.dest_location.id,
        )
        with self.assertRaises(UserError):
            req.with_user(self.stock_mgr_user).action_internal_transfer()

    def test_action_internal_transfer_no_dest_raises(self):
        """Missing destination location raises UserError."""
        req = self._make_request(
            status='approved',
            source_location_id=self.src_location.id,
        )
        with self.assertRaises(UserError):
            req.with_user(self.stock_mgr_user).action_internal_transfer()

    def test_action_internal_transfer_wrong_state_raises(self):
        """Internal transfer on a non-approved request raises UserError."""
        req = self._make_request(
            status='waiting',
            source_location_id=self.src_location.id,
            destination_location_id=self.dest_location.id,
        )
        with self.assertRaises(UserError):
            req.with_user(self.stock_mgr_user).action_internal_transfer()

    def test_action_internal_transfer_wrong_group_raises(self):
        """Non-stock-manager cannot create internal transfer."""
        req = self._make_request(
            status='approved',
            source_location_id=self.src_location.id,
            destination_location_id=self.dest_location.id,
        )
        with self.assertRaises(UserError):
            req.with_user(self.plain_user).action_internal_transfer()

    # ------------------------------------------------------------------
    # action_expense
    # ------------------------------------------------------------------

    def test_action_expense_success_creates_expenses(self):
        """Dept manager can generate expenses for a waiting request."""
        req = self._make_request(status='waiting')
        self.env['damage.detail'].create({
            'product_id': self.product.id,
            'unit_price': 100.0,
            'quantity': 2,
            'equipment_damage_id': req.id,
        })
        req.with_user(self.dept_mgr_user).action_expense()
        self.assertTrue(req.is_expensed)
        expenses = req.equipment_expense_ids
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses.employee_id, self.employee)
        self.assertEqual(expenses.product_id, self.product)
        self.assertEqual(expenses.name, req.name)
        # Total is the damage subtotal (unit price x quantity)
        self.assertAlmostEqual(expenses.total_amount_currency, 200.0)
        self.assertEqual(expenses.quantity, 2)

    def test_action_expense_no_damage_no_expense(self):
        """Without damage lines no expense is created."""
        req = self._make_request(status='waiting')
        req.with_user(self.dept_mgr_user).action_expense()
        self.assertFalse(req.is_expensed)

    def test_action_expense_wrong_state_raises(self):
        """Expense creation on a non-waiting request raises UserError."""
        req = self._make_request(status='approved')
        with self.assertRaises(UserError):
            req.with_user(self.dept_mgr_user).action_expense()

    def test_action_expense_wrong_group_raises(self):
        """Non-dept-manager cannot generate expenses."""
        req = self._make_request(status='waiting')
        with self.assertRaises(UserError):
            req.with_user(self.plain_user).action_expense()

    # ------------------------------------------------------------------
    # action_smart_expense
    # ------------------------------------------------------------------

    def test_action_smart_expense_returns_action(self):
        """action_smart_expense should return a window action dict."""
        req = self._make_request()
        result = req.action_smart_expense()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'hr.expense')

    # ------------------------------------------------------------------
    # action_view_internal_transfer
    # ------------------------------------------------------------------

    def test_action_view_internal_transfer_returns_action(self):
        """action_view_internal_transfer should return a window action dict."""
        req = self._make_request(
            status='approved',
            source_location_id=self.src_location.id,
            destination_location_id=self.dest_location.id,
        )
        self.env['equipment.detail'].create({
            'product_id': self.product.id,
            'quantity': 1,
            'equipment_detail_id': req.id,
        })
        # Create a picking linked to this request so res_id is populated
        req.with_user(self.stock_mgr_user).action_internal_transfer()
        result = req.action_view_internal_transfer()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'stock.picking')
        self.assertTrue(result.get('res_id'))

    def test_action_view_internal_transfer_no_picking(self):
        """The action is returned even when no picking is linked."""
        req = self._make_request()
        result = req.action_view_internal_transfer()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'stock.picking')
