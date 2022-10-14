# -*- coding: utf-8 -*-
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipRunCron(models.Model):
    """
    Automate payslip generation
     1.Month First
     2.Specific Date
     3.Month End
    """
    _inherit = 'hr.payslip.run'

    @api.onchange('generate_payslip')
    def _check(self):
        """Check the options and call the corresponding methods"""
        if self.env['ir.config_parameter'].sudo().get_param('generate_payslip'):
            if self.env['ir.config_parameter'].sudo().get_param(
                    'option', 'first') == 'first':
                self.month_first()
            elif self.env['ir.config_parameter'].sudo().get_param(
                    'option', 'specific') == 'specific':
                self.specific_date()
            elif self.env['ir.config_parameter'].sudo().get_param(
                    'option', 'end') == 'end':
                self.month_end()
        else:
            raise UserError(_("Enable configuration settings"))

    def month_first(self):
        """Method for automate month first option"""
        today = fields.Date.today()
        day = today.day
        if day == 1:
            self.generate_payslips()
        else:
            raise UserError(_("Today is not month first"))
            pass

    def month_end(self):
        """Method for automate month end option"""
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
        """Method for automate specific day option"""
        val = int(self.env['ir.config_parameter'].sudo().get_param('generate_day'))
        today = fields.Date.today()
        day = today.day
        if day == val:
            self.generate_payslips()
        else:
            raise UserError(_("Can't generate payslips today"))
            pass

    def generate_payslips(self):
        """Method for generate payslip batches and payslips,
        before that you must assign ongoing contracts for employees"""
        batch_id = self.create([{
            'name': 'Payslip Batch For ' + date.today().strftime('%B')
                    + ' ' + str(date.today().year),
            'date_start': fields.Date.to_string(date.today().replace(day=1)),
            'date_end': fields.Date.to_string(
                (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date())
        }])

        generate_payslip = self.env['hr.payslip.employees']
        # print(generate_payslip)
        contract_ids = self.env['hr.contract'].search([('state', '=', 'open')])
        employee_ids = []
        for line in contract_ids:
            print(line.employee_id.name)
            employee_ids.append(line.employee_id)
            generate_payslip.create({
                'employee_ids': [(4, line.employee_id.id)]
            })
            # generate_payslip.create([{
            #         'name': line.employee_id.name,
            #         'work_phone': line.employee_id.work_phone or None,
            #         'work_email': line.employee_id.work_email or None,
            #         'department_id': line.employee_id.department_id or None,
            #         'job_id': line.employee_id.job_id or None,
            #         'parent_id': line.employee_id.parent_id.name or None,
            # }])
            print(generate_payslip)
        payslips = self.env['hr.payslip']
        [run_data] = batch_id.read(
            ['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not employee_ids:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in employee_ids:
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id,
                                                                    contract_id=False)
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
                'company_id': employee.company_id.id,
            }
            payslips += self.env['hr.payslip'].create(res)
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}
