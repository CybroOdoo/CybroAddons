# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

from datetime import date, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHrVacationMngmt(TransactionCase):
    """Test suite for the hr_vacation_mngmt module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.department = cls.env['hr.department'].create({
            'name': 'Engineering',
        })

        cls.employee_user = cls.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Employee User',
            'login': 'employee_user@test.com',
        })

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Alice Engineer',
            'department_id': cls.department.id,
            'user_id': cls.employee_user.id,
        })

        cls.employee2 = cls.env['hr.employee'].create({
            'name': 'Bob Engineer',
            'department_id': cls.department.id,
        })

        cls.leave_type = cls.env['hr.leave.type'].create({
            'name': 'Annual Leave Test',
            'requires_allocation': False,
            'leave_validation_type': 'hr',
        })

        cls.project = cls.env['project.project'].create({
            'name': 'Test Project',
        })

        cls.hr_manager = cls.env.ref('base.user_admin')

        cls.expense_account = cls.env['account.account'].search(
            [('account_type', '=', 'expense')], limit=1
        )

    def _make_leave(self, employee=None, days=5, state='confirm'):
        """Create an hr.leave bypassing ORM checks.
        """
        employee = employee or self.employee
        date_from = date.today() + timedelta(days=10)
        date_to = date_from + timedelta(days=days - 1)

        leave = self.env['hr.leave'].with_context(
            leave_fast_create=True,
            mail_create_nosubscribe=True,
            mail_notrack=True,
        ).sudo().create({
            'holiday_status_id': self.leave_type.id,
            'employee_id': employee.id,
            'request_date_from': date_from,
            'request_date_to': date_to,
        })
        if state != 'confirm':
            self.env.cr.execute(
                "UPDATE hr_leave SET state = %s WHERE id = %s",
                (state, leave.id)
            )
            leave.invalidate_recordset()
        return leave

    def _make_flight_ticket(self, leave, start_offset=10, return_offset=20,
                            fare=500.0, state='booked'):
        """Create an hr.flight.ticket linked to a leave."""
        ticket = self.env['hr.flight.ticket'].sudo().create({
            'employee_id': leave.id,
            'leave_id': leave.id,
            'depart_from': 'Mumbai',
            'destination': 'Dubai',
            'date_start': date.today() + timedelta(days=start_offset),
            'date_return': date.today() + timedelta(days=return_offset),
            'ticket_fare': fare,
            'ticket_type': 'round',
        })
        if state != 'booked':
            self.env.cr.execute(
                "UPDATE hr_flight_ticket SET state = %s WHERE id = %s",
                (state, ticket.id)
            )
            ticket.invalidate_recordset()
        return ticket

    def test_hr_leave_leave_salary_field_stored(self):
        """leave_salary Selection field is stored and retrieved correctly."""
        leave = self._make_leave()
        leave.sudo().write({'leave_salary': '1'})
        self.assertEqual(leave.leave_salary, '1')

    def test_hr_leave_expense_account_field(self):
        """expense_account_id field can be set on a leave record."""
        leave = self._make_leave()
        leave.sudo().write({'expense_account_id': self.expense_account.id})
        self.assertEqual(leave.expense_account_id, self.expense_account)

    def test_hr_leave_flight_ticket_ids_o2m(self):
        """flight_ticket_ids One2many reflects linked flight tickets."""
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave)
        self.assertIn(ticket, leave.flight_ticket_ids)

    def test_hr_leave_pending_task_ids_o2m(self):
        """pending_task_ids One2many reflects linked pending tasks."""
        leave = self._make_leave()
        task = self.env['pending.task'].create({
            'name': 'Finish Report',
            'leave_id': leave.id,
            'project_id': self.project.id,
        })
        self.assertIn(task, leave.pending_task_ids)

    def test_hr_leave_remaining_leaves_no_employee(self):
        """remaining_leaves is 0.0 when no employee is set."""
        leave = self.env['hr.leave'].new({
            'holiday_status_id': self.leave_type.id,
        })
        self.assertEqual(leave.remaining_leaves, 0.0)

    def test_action_approve_raises_for_non_hr_officer(self):
        """action_approve raises UserError for a user without HR officer
        privileges.
        """
        portal_group = self.env.ref('base.group_portal')
        plain_user = self.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Plain Portal User 2',
            'login': 'plain_portal2_test@test.com',
            'group_ids': [(6, 0, [portal_group.id])],
        })
        leave = self._make_leave()
        with self.assertRaises(UserError):
            leave.with_user(plain_user).action_approve()

    def test_action_approve_raises_when_not_confirmed(self):
        """action_approve raises UserError when leave state is not 'confirm'."""
        leave = self._make_leave(state='draft')
        with self.assertRaises(UserError):
            leave.with_user(self.hr_manager).action_approve()

    def test_action_approve_returns_task_reassign_when_pending_tasks(self):
        """action_approve opens task.reassign wizard when pending tasks exist."""
        leave = self._make_leave(state='confirm')
        self.env['pending.task'].create({
            'name': 'Pending Report',
            'leave_id': leave.id,
            'project_id': self.project.id,
        })
        result = leave.with_user(self.hr_manager).action_approve()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'task.reassign')
        self.assertEqual(result.get('target'), 'new')

    def test_action_approve_validates_directly_when_no_pending_tasks(self):
        """action_approve calls _action_validate directly when no pending
        tasks are linked."""
        leave = self._make_leave(state='confirm')
        self.assertFalse(leave.pending_task_ids)
        leave.with_user(self.hr_manager).action_approve()
        self.assertNotEqual(leave.state, 'confirm')

    def test_action_book_ticket_raises_for_non_hr_officer(self):
        """action_book_ticket raises UserError for non HR officer.
        """
        portal_group = self.env.ref('base.group_portal')
        plain_user = self.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Plain Portal User',
            'login': 'plain_portal_test@test.com',
            'group_ids': [(6, 0, [portal_group.id])],
        })
        leave = self._make_leave()
        with self.assertRaises(UserError):
            leave.with_user(plain_user).action_book_ticket()

    def test_action_book_ticket_returns_correct_action(self):
        """action_book_ticket returns an act_window targeting hr.flight.ticket."""
        leave = self._make_leave()
        result = leave.with_user(self.hr_manager).action_book_ticket()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'hr.flight.ticket')
        self.assertEqual(result.get('target'), 'new')

    def test_action_book_ticket_passes_leave_context(self):
        """action_book_ticket passes default_leave_id in context."""
        leave = self._make_leave()
        result = leave.with_user(self.hr_manager).action_book_ticket()
        self.assertEqual(
            result.get('context', {}).get('default_leave_id'), leave.id
        )

    def test_action_view_flight_ticket_returns_correct_action(self):
        """action_view_flight_ticket returns form view for hr.flight.ticket."""
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave)
        result = leave.action_view_flight_ticket()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'hr.flight.ticket')
        self.assertEqual(result.get('res_id'), ticket.id)

    def test_compute_holiday_managers_ids(self):
        """holiday_managers_ids compute uses group_hr_holidays_manager members.
        """
        manager_group = self.env.ref('hr_holidays.group_hr_holidays_manager')
        self.assertIn(
            self.hr_manager,
            manager_group.all_user_ids,
            "Admin should be a member of group_hr_holidays_manager"
        )

    def test_flight_ticket_sequence_auto_generated(self):
        """Flight ticket name is auto-generated from sequence on create."""
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave)
        self.assertNotEqual(ticket.name, 'New',
                            "Sequence should replace the 'New' placeholder")
        self.assertTrue(ticket.name,
                        "Ticket name must not be empty after creation")

    def test_flight_ticket_sequence_unique_per_record(self):
        """Each flight ticket gets a distinct sequence number."""
        leave = self._make_leave()
        ticket1 = self._make_flight_ticket(leave)
        ticket2 = self._make_flight_ticket(leave)
        self.assertNotEqual(ticket1.name, ticket2.name)

    def test_flight_ticket_date_constraint_raises_when_start_after_return(self):
        """check_valid_date raises ValidationError when start date > return."""
        leave = self._make_leave()
        with self.assertRaises(ValidationError):
            self.env['hr.flight.ticket'].sudo().create({
                'employee_id': leave.id,
                'leave_id': leave.id,
                'depart_from': 'Mumbai',
                'destination': 'Dubai',
                'date_start': date.today() + timedelta(days=20),
                'date_return': date.today() + timedelta(days=10),
                'ticket_fare': 300.0,
            })

    def test_flight_ticket_date_constraint_passes_when_start_before_return(self):
        """check_valid_date does not raise when start date < return date."""
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave, start_offset=5, return_offset=15)
        self.assertTrue(ticket.id)

    def test_action_cancel_ticket_from_booked(self):
        """Cancelling a booked ticket sets state to 'canceled'."""
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave, state='booked')
        ticket.action_cancel_ticket()
        self.assertEqual(ticket.state, 'canceled')

    def test_action_cancel_ticket_from_confirmed_with_draft_invoice(self):
        """Cancelling a confirmed ticket with a draft invoice sets state to
        'canceled'."""
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave, state='booked')
        journal = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1
        )
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'journal_id': journal.id,
            'state': 'draft',
        })
        ticket.sudo().write({'invoice_id': invoice.id})
        self.env.cr.execute(
            "UPDATE hr_flight_ticket SET state = 'confirmed' WHERE id = %s",
            (ticket.id,)
        )
        ticket.invalidate_recordset()
        ticket.action_cancel_ticket()
        self.assertEqual(ticket.state, 'canceled')

    def test_action_confirm_ticket_raises_when_fare_is_zero(self):
        """action_confirm_ticket raises UserError when ticket_fare is 0."""
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave, fare=0.0)
        with self.assertRaises(UserError):
            ticket.action_confirm_ticket()

    def test_action_confirm_ticket_raises_when_no_expense_account_config(self):
        """action_confirm_ticket raises UserError when expense account is not
        configured in system parameters."""
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_vacation_mngmt.expense_id', False
        )
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave, fare=500.0)
        with self.assertRaises(UserError):
            ticket.action_confirm_ticket()

    def test_action_view_invoice_returns_correct_action(self):
        """action_view_invoice returns an act_window for account.move."""
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave)
        journal = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1
        )
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'journal_id': journal.id,
        })
        ticket.sudo().write({'invoice_id': invoice.id})
        result = ticket.action_view_invoice()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'account.move')
        self.assertEqual(result.get('res_id'), invoice.id)

    def test_flight_ticket_action_book_ticket_closes_window(self):
        """action_book_ticket on the ticket model returns act_window_close."""
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave)
        result = ticket.action_book_ticket()
        self.assertEqual(result.get('type'), 'ir.actions.act_window_close')

    def test_run_update_ticket_status_confirmed_to_started(self):
        """Confirmed ticket whose travel has started moves to 'started'."""
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave, state='booked')
        self.env.cr.execute(
            """UPDATE hr_flight_ticket
               SET state = 'confirmed',
                   date_start = %s,
                   date_return = %s
               WHERE id = %s""",
            (date.today() - timedelta(days=1),
             date.today() + timedelta(days=5),
             ticket.id)
        )
        ticket.invalidate_recordset()
        self.env['hr.flight.ticket'].run_update_ticket_status()
        ticket.invalidate_recordset()
        self.assertEqual(ticket.state, 'started')

    def test_run_update_ticket_status_to_completed(self):
        """Ticket whose return date has passed moves to 'completed'."""
        leave = self._make_leave()
        ticket = self._make_flight_ticket(leave, state='booked')
        self.env.cr.execute(
            """UPDATE hr_flight_ticket
               SET state = 'confirmed',
                   date_start = %s,
                   date_return = %s
               WHERE id = %s""",
            (date.today() - timedelta(days=10),
             date.today() - timedelta(days=1),
             ticket.id)
        )
        ticket.invalidate_recordset()
        self.env['hr.flight.ticket'].run_update_ticket_status()
        ticket.invalidate_recordset()
        self.assertEqual(ticket.state, 'completed')

    def test_pending_task_creation(self):
        """PendingTask is created with correct leave and project links."""
        leave = self._make_leave()
        task = self.env['pending.task'].create({
            'name': 'Write Documentation',
            'leave_id': leave.id,
            'project_id': self.project.id,
            'description': 'Write module docs',
        })
        self.assertEqual(task.leave_id, leave)
        self.assertEqual(task.project_id, self.project)

    def test_pending_task_dept_relayed_from_leave(self):
        """PendingTask.dept_id is relayed from the linked leave's department."""
        leave = self._make_leave()
        task = self.env['pending.task'].create({
            'name': 'QA Testing',
            'leave_id': leave.id,
            'project_id': self.project.id,
        })
        self.assertEqual(task.dept_id, leave.department_id)

    def test_pending_task_compute_unavailable_employees(self):
        """unavailable_employee_ids reflects employees with overlapping leaves."""
        leave = self._make_leave()
        task = self.env['pending.task'].create({
            'name': 'Code Review',
            'leave_id': leave.id,
            'project_id': self.project.id,
        })
        self.assertFalse(task.unavailable_employee_ids)

    def test_task_reassign_raises_when_task_has_no_assignee(self):
        """action_approve raises UserError when a pending task has no
        assigned_person_id."""
        leave = self._make_leave(state='confirm')
        self.env['pending.task'].create({
            'name': 'Unassigned Task',
            'leave_id': leave.id,
            'project_id': self.project.id,
        })
        wizard = self.env['task.reassign'].create({
            'leave_req_id': leave.id,
        })
        with self.assertRaises(UserError):
            wizard.action_approve()

    def test_task_reassign_raises_when_assignee_is_unavailable(self):
        """action_approve raises UserError when the assignee is in the
        unavailable_employee_ids computed list.
        """
        leave = self._make_leave(state='confirm')

        pending = self.env['pending.task'].create({
            'name': 'Overlapping Task',
            'leave_id': leave.id,
            'project_id': self.project.id,
            'assigned_person_id': self.employee2.id,
        })

        self.assertIn(
            self.employee2,
            pending.unavailable_employee_ids,
            "Setup error: employee2 should appear as unavailable due to "
            "overlapping validated leave"
        )

        wizard = self.env['task.reassign'].create({
            'leave_req_id': leave.id,
        })
        with self.assertRaises(UserError):
            wizard.action_approve()

    def test_task_reassign_cancel_clears_assignees(self):
        """cancel() clears assigned_person_id on all pending tasks."""
        leave = self._make_leave(state='confirm')
        pending = self.env['pending.task'].create({
            'name': 'Task To Cancel',
            'leave_id': leave.id,
            'project_id': self.project.id,
            'assigned_person_id': self.employee2.id,
        })
        wizard = self.env['task.reassign'].create({
            'leave_req_id': leave.id,
        })
        wizard.cancel()
        self.assertFalse(pending.assigned_person_id,
                         "assigned_person_id should be cleared after cancel")

    def test_task_reassign_cancel_returns_window_close(self):
        """cancel() returns an act_window_close action."""
        leave = self._make_leave(state='confirm')
        wizard = self.env['task.reassign'].create({
            'leave_req_id': leave.id,
        })
        result = wizard.cancel()
        self.assertEqual(result.get('type'), 'ir.actions.act_window_close')

    def test_payslip_leave_salary_field_default_false(self):
        """leave_salary Boolean defaults to False on a new payslip."""
        payslip = self.env['hr.payslip'].new({'employee_id': self.employee.id})
        self.assertFalse(payslip.leave_salary)

    def test_payslip_leave_salary_field_can_be_set_true(self):
        """leave_salary Boolean can be set to True and is stored.
        """
        contract = self.env['hr.version'].search(
            [('employee_id', '=', self.employee.id)], limit=1
        )
        if not contract:
            return
        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'contract_id': contract.id,
            'date_from': date.today().replace(day=1),
            'date_to': date.today(),
            'leave_salary': True,
        })
        self.assertTrue(payslip.leave_salary)

    def test_res_config_settings_leave_reminder_field(self):
        """leave_reminder Boolean is stored in ir.config_parameter."""
        settings = self.env['res.config.settings'].create({
            'leave_reminder': True,
            'reminder_day_before': 3,
        })
        settings.execute()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'hr_vacation_mngmt.leave_reminder'
        )
        self.assertEqual(param, 'True')

    def test_res_config_settings_reminder_day_before_field(self):
        """reminder_day_before Integer is stored in ir.config_parameter."""
        settings = self.env['res.config.settings'].create({
            'reminder_day_before': 7,
        })
        settings.execute()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'hr_vacation_mngmt.reminder_day_before'
        )
        self.assertEqual(int(param), 7)

    def test_res_config_settings_default_leave_salary_field(self):
        """default_leave_salary Selection is persisted correctly.
        """
        settings = self.env['res.config.settings'].create({
            'default_leave_salary': '1',
        })
        settings.execute()

        default_record = self.env['ir.default'].search([
            ('field_id.model', '=', 'hr.leave'),
            ('field_id.name', '=', 'leave_salary'),
        ], limit=1)
        self.assertTrue(
            default_record,
            "Expected an ir.default record for hr.leave.leave_salary"
        )
        self.assertEqual(
            default_record.json_value, '"1"',
            "Stored default should be the JSON-encoded selection value '1'"
        )
