# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
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
#############################################################################
from datetime import date
from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHrPayslipRun(TransactionCase):

    def setUp(self):
        super().setUp()
        self.PayslipRun = self.env['hr.payslip.run']
        self.config = self.env['ir.config_parameter'].sudo()

        self.employee = self.env['hr.employee'].create({
            'name': 'Test Payroll Employee',
        })
        if 'hr.contract' in self.env:
            struct = False
            if 'hr.payroll.structure' in self.env:
                struct = self.env['hr.payroll.structure'].search([], limit=1)
                if not struct:
                    struct = self.env['hr.payroll.structure'].create({
                        'name': 'Test Salary Structure',
                        'code': 'TEST_STRUCT',
                    })
            contract_vals = {
                'name': 'Test Contract',
                'employee_id': self.employee.id,
                'wage': 5000.0,
                'state': 'open',
                'date_start': fields.Date.today() - relativedelta(months=1),
            }
            if 'struct_id' in self.env['hr.contract']._fields and struct:
                contract_vals['struct_id'] = struct.id
            if ('structure_type_id' in self.env['hr.contract']._fields and
                    'hr.payroll.structure.type' in self.env):
                st = self.env['hr.payroll.structure.type'].search([], limit=1)
                if st:
                    contract_vals['structure_type_id'] = st.id
            self.contract = self.env['hr.contract'].create(contract_vals)

    @patch(
        'odoo.addons.automatic_payroll.models.hr_payslip_run.HrPayslipRun.'
        'month_first')
    def test_check_options_not_enabled(self, mock_month_first):
        self.config.set_param('automatic_payroll.generate_payslip', False)
        self.PayslipRun._check_options()
        mock_month_first.assert_not_called()

    @patch(
        'odoo.addons.automatic_payroll.models.hr_payslip_run.HrPayslipRun.'
        'month_first')
    def test_check_options_first(self, mock_month_first):
        self.config.set_param('automatic_payroll.generate_payslip', True)
        self.config.set_param('automatic_payroll.option', 'first')
        self.PayslipRun._check_options()
        mock_month_first.assert_called_once()

    @patch(
        'odoo.addons.automatic_payroll.models.hr_payslip_run.HrPayslipRun.'
        'specific_date')
    def test_check_options_specific(self, mock_specific_date):
        self.config.set_param('automatic_payroll.generate_payslip', True)
        self.config.set_param('automatic_payroll.option', 'specific')
        self.PayslipRun._check_options()
        mock_specific_date.assert_called_once()

    @patch(
        'odoo.addons.automatic_payroll.models.hr_payslip_run.HrPayslipRun.'
        'month_end')
    def test_check_options_end(self, mock_month_end):
        self.config.set_param('automatic_payroll.generate_payslip', True)
        self.config.set_param('automatic_payroll.option', 'end')
        self.PayslipRun._check_options()
        mock_month_end.assert_called_once()

    @patch('odoo.fields.Date.today')
    def test_month_first(self, mock_today):
        # Test when day is 1
        mock_today.return_value = date(2025, 1, 1)
        initial_batches = self.PayslipRun.search_count([])
        self.PayslipRun.month_first()
        self.assertEqual(
            self.PayslipRun.search_count([]), initial_batches + 1)

        # Test when day is not 1
        mock_today.return_value = date(2025, 1, 2)
        batches_before = self.PayslipRun.search_count([])
        self.PayslipRun.month_first()
        self.assertEqual(self.PayslipRun.search_count([]), batches_before)

    @patch('odoo.fields.Date.today')
    def test_month_end(self, mock_today):
        # Test when day is last day of the month
        mock_today.return_value = date(2025, 1, 31)
        initial_batches = self.PayslipRun.search_count([])
        self.PayslipRun.month_end()
        self.assertEqual(
            self.PayslipRun.search_count([]), initial_batches + 1)

        # Test when day is not last day of the month
        mock_today.return_value = date(2025, 1, 30)
        batches_before = self.PayslipRun.search_count([])
        self.PayslipRun.month_end()
        self.assertEqual(self.PayslipRun.search_count([]), batches_before)

    @patch('odoo.fields.Date.today')
    def test_specific_date(self, mock_today):
        self.config.set_param('automatic_payroll.generate_day', '15')

        # Test when day matches
        mock_today.return_value = date(2025, 1, 15)
        initial_batches = self.PayslipRun.search_count([])
        self.PayslipRun.specific_date()
        self.assertEqual(
            self.PayslipRun.search_count([]), initial_batches + 1)

        # Test when day does not match
        mock_today.return_value = date(2025, 1, 16)
        batches_before = self.PayslipRun.search_count([])
        self.PayslipRun.specific_date()
        self.assertEqual(self.PayslipRun.search_count([]), batches_before)

    def test_generate_payslips(self):
        """Test actual creation of payslip batch and employee payslips."""
        initial_batches = self.PayslipRun.search_count([])
        result = self.PayslipRun.generate_payslips()
        self.assertEqual(result.get('type'), 'ir.actions.act_window_close')

        batches = self.PayslipRun.search([], order='id desc', limit=1)
        self.assertEqual(
            self.PayslipRun.search_count([]), initial_batches + 1)
        self.assertTrue(batches.name.startswith('Payslip Batch For'))

        payslips = self.env['hr.payslip'].search([
            ('payslip_run_id', '=', batches.id)
        ])
        self.assertGreater(len(payslips), 0)
        self.assertIn(self.employee, payslips.mapped('employee_id'))

    def test_generate_payslips_no_employees(self):
        """Test UserError raised and no batch created when no employees."""
        if 'hr.contract' in self.env:
            self.env['hr.contract'].search(
                [('state', '=', 'open')]).write({'state': 'close'})
        else:
            self.env['hr.employee'].search(
                [('active', '=', True)]).write({'active': False})
        initial_batches = self.PayslipRun.search_count([])
        with self.assertRaises(UserError):
            self.PayslipRun.generate_payslips()
        self.assertEqual(self.PayslipRun.search_count([]), initial_batches)
