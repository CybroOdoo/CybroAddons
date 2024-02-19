# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, _
from odoo.exceptions import UserError


class HrPayslipRun(models.Model):
    """ Automation of payslip generation based on specified options:
     1.Month First
     2.Specific Date
     3.Month End """
    _inherit = 'hr.payslip.run'

    def _check_options(self):
        """Check the options and call the corresponding methods."""
        if self.env['ir.config_parameter'].sudo().get_param('automatic_payroll.generate_payslip'):
            if self.env['ir.config_parameter'].sudo().get_param(
                    'automatic_payroll.option', 'first') == 'first':
                self.month_first()
            elif self.env['ir.config_parameter'].sudo().get_param(
                    'automatic_payroll.option', 'specific') == 'specific':
                self.specific_date()
            elif self.env['ir.config_parameter'].sudo().get_param(
                    'automatic_payroll.option', 'end') == 'end':
                self.month_end()
        else:
            raise UserError(_("Enable configuration settings"))

    def month_first(self):
        """Automates payslip generation for the 'Month First' option."""
        today = fields.Date.today()
        day = today.day
        if day == 1:
            self.generate_payslips()
        else:
            raise UserError(_("Today is not month first"))
            pass

    def month_end(self):
        """Automates payslip generation for the 'Month End' option"""
        today = fields.Date.today()
        day_today = today.day
        last_date = today + relativedelta(day=1, months=+1, days=-1)
        last_day = last_date.day
        if day_today == last_day:
            self.generate_payslips()
        else:
            raise UserError(_("Today is not month end"))
            pass

    def specific_date(self):
        """Automates payslip generation for the 'Specific date' option"""
        val = int(self.env['ir.config_parameter'].sudo().get_param('automatic_payroll.generate_day'))
        today = fields.Date.today()
        day = today.day
        if day == val:
            self.generate_payslips()
        else:
            raise UserError(_("Can't generate payslips today"))

    def generate_payslips(self):
        """Method for generate payslip batches and payslips,
        before that you must assign ongoing contracts for employees."""
        batch_id = self.create([{
            'name': 'Payslip Batch For ' + date.today().strftime(
                '%B') + ' ' + str(date.today().year),
            'date_start': fields.Date.to_string(date.today().replace(day=1)),
            'date_end': fields.Date.to_string((datetime.now() + relativedelta(
                months=+1, day=1, days=-1)).date())}])
        generate_payslip = self.env['hr.payslip.employees']
        contract_ids = self.env['hr.contract'].search([('state', '=', 'open')])
        employee_ids = []
        for line in contract_ids:
            employee_ids.append(line.employee_id)
            generate_payslip.create(
                {'employee_ids': [(4, line.employee_id.id)]})
        payslips = self.env['hr.payslip']
        [run_data] = batch_id.read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not employee_ids:
            raise UserError(_("You must select employees to generate payslip."))
        for employee in employee_ids:
            slip_data = self.env['hr.payslip'].onchange_employee_id(
                from_date, to_date, employee.id, contract_id=False)
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': batch_id.id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [
                    (0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id}
            payslips += self.env['hr.payslip'].create(res)
        payslips.action_compute_sheet()
        return {'type': 'ir.actions.act_window_close'}
