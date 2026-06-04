from datetime import datetime
from unittest.mock import patch

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountAnalyticLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager_employee = cls.env['hr.employee'].create({
            'name': 'Timesheet Report Manager',
            'work_email': 'timesheet.manager@example.com',
        })
        cls.cc_employee = cls.env['hr.employee'].create({
            'name': 'Timesheet Report CC',
            'work_email': 'timesheet.cc@example.com',
        })
        cls.timesheet_employee = cls.env['hr.employee'].create({
            'name': 'Timesheet Report Employee',
            'work_email': 'timesheet.employee@example.com',
        })
        cls.project = cls.env['project.project'].create({
            'name': 'Timesheet Report Project',
            'allow_timesheets': True,
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Timesheet Report Task',
            'project_id': cls.project.id,
        })

    def setUp(self):
        super().setUp()
        self.params = self.env['ir.config_parameter'].sudo()
        self.params.set_param(
            'work_report_from_timesheet.employee_id',
            self.manager_employee.id,
        )
        self.params.set_param(
            'work_report_from_timesheet.employee_ids',
            [self.cc_employee.id],
        )

    def _create_timesheet(self, name='Timesheet report line'):
        return self.env['account.analytic.line'].create({
            'name': name,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'employee_id': self.timesheet_employee.id,
            'unit_amount': 2.0,
            'date': fields.Date.today(),
        })

    def test_write_sends_task_report_when_enabled(self):
        timesheet = self._create_timesheet()
        self.params.set_param(
            'work_report_from_timesheet.is_generate_work_report',
            True,
        )
        self.params.set_param(
            'work_report_from_timesheet.report_method',
            'task_report',
        )

        with patch.object(
                type(timesheet), '_send_daily_task_report', return_value=None
        ) as send_task_report:
            result = timesheet.write({'status': 'completed'})

        self.assertTrue(result)
        send_task_report.assert_called_once_with()

    def test_write_does_not_send_task_report_for_daily_report_method(self):
        timesheet = self._create_timesheet()
        self.params.set_param(
            'work_report_from_timesheet.is_generate_work_report',
            True,
        )
        self.params.set_param(
            'work_report_from_timesheet.report_method',
            'daily_report',
        )

        with patch.object(
                type(timesheet), '_send_daily_task_report', return_value=None
        ) as send_task_report:
            timesheet.write({'status': 'completed'})

        send_task_report.assert_not_called()

    def test_send_daily_task_report_uses_configured_recipients(self):
        timesheet = self._create_timesheet()
        template = self.env.ref(
            'work_report_from_timesheet.email_template_work_report_from_timesheet'
        )

        with patch.object(
                type(template), 'send_mail', autospec=True, return_value=True
        ) as send_mail:
            timesheet._send_daily_task_report()

        send_mail.assert_called_once()
        args, kwargs = send_mail.call_args
        self.assertEqual(args[1], timesheet.id)
        self.assertTrue(kwargs['force_send'])
        self.assertEqual(kwargs['email_values']['email_to'],
                         self.manager_employee.work_email)
        self.assertEqual(kwargs['email_values']['email_cc'],
                         self.cc_employee.work_email)
        self.assertEqual(kwargs['email_values']['email_from'],
                         self.timesheet_employee.work_email)
        self.assertEqual(kwargs['email_values']['model'],
                         'account.analytic.line')
        self.assertEqual(kwargs['email_values']['res_id'], timesheet.id)

    def test_send_employee_daily_work_report_sends_one_mail_per_employee(self):
        self.params.set_param(
            'work_report_from_timesheet.is_generate_work_report',
            True,
        )
        self.params.set_param(
            'work_report_from_timesheet.report_method',
            'daily_report',
        )
        timesheet = self._create_timesheet('Daily report line')
        template = self.env.ref(
            'work_report_from_timesheet.email_template_daily_report_from_timesheet'
        )
        self.env['account.analytic.line'].search([
            ('date', '=', fields.Date.today()),
            ('id', '!=', timesheet.id),
        ]).write({'date': '2000-01-01'})

        with patch.object(
                type(template), 'send_mail', autospec=True, return_value=True
        ) as send_mail:
            self.env['account.analytic.line'].send_employee_daily_work_report()

        send_mail.assert_called_once()
        _args, kwargs = send_mail.call_args
        expected_subject = (
            f"Daily work report_{datetime.today().date().strftime('%b-%d-%Y')}"
            f"_{timesheet.employee_id.name}"
        )
        self.assertEqual(kwargs['res_id'], timesheet.id)
        self.assertTrue(kwargs['force_send'])
        self.assertEqual(kwargs['email_values']['email_to'],
                         self.manager_employee.work_email)
        self.assertEqual(kwargs['email_values']['email_cc'],
                         self.cc_employee.work_email)
        self.assertEqual(kwargs['email_values']['email_from'],
                         timesheet.employee_id.work_email)
        self.assertEqual(kwargs['email_values']['subject'], expected_subject)

    def test_send_employee_daily_work_report_skips_other_report_methods(self):
        self.params.set_param(
            'work_report_from_timesheet.is_generate_work_report',
            True,
        )
        self.params.set_param(
            'work_report_from_timesheet.report_method',
            'task_report',
        )
        template = self.env.ref(
            'work_report_from_timesheet.email_template_daily_report_from_timesheet'
        )

        with patch.object(
                type(template), 'send_mail', autospec=True, return_value=True
        ) as send_mail:
            self.env['account.analytic.line'].send_employee_daily_work_report()

        send_mail.assert_not_called()
