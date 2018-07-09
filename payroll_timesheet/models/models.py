# -*- coding: utf-8 -*-

import itertools
from odoo import models, fields, api


class PayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    timesheet_structure = fields.Boolean(string='Timesheet Based Structure', default=False,
                                         help='Flag Which says the Structure is based on Timesheets submitted by employee')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    timesheet_payroll = fields.Boolean(string='Timesheet Based Payroll', default=False,
                                       help='Flag Which says the payroll is based on Timesheets submitted by employee')

    @api.onchange('timesheet_payroll')
    def onchange_timesheet_payroll(self):
        if self.timesheet_payroll:
            self.struct_id = False
            return {
                'domain': {
                    'struct_id': [('timesheet_structure', '=', True)]
                },
            }
        else:
            return {
                'domain': {'struct_id': []},
            }


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    timesheet_hours = fields.Integer(string='Timesheet Hours',  states={'done': [('readonly', True)]},
                                     help='Total Timesheet hours approved for employee.')
    total_hours = fields.Integer(string='Total Hours', states={'done': [('readonly', True)]},
                                 help='Total Hours By Working schedule')
    timesheet_payroll = fields.Boolean(related='contract_id.timesheet_payroll')

    def compute_timesheet_hours(self, contract_id, date_from, date_to):
        """
        Function which computes total hours, timesheethours, attendances, timehseet difference,
        :param employee_id:
        :param date_from:
        :param date_to:
        :return:  computed total timesheet hours within duration, total hours by working schedule
        """
        if not contract_id:
            return {}
        env = self.env
        employee_id = contract_id.employee_id
        timesheet_object = env['hr_timesheet_sheet.sheet']
        total_hours = 0.0
        timesheet_hours = timesheet_attendance = timesheet_difference = 0.0
        for line in self.worked_days_line_ids:
            total_hours += line.number_of_hours if line.code == 'WORK100' else 0.0
        sheets = timesheet_object.search([
            ('employee_id', '=', employee_id.id),
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('state', '=', 'done')

        ])
        period_ids = []
        period_ids += [sheet.period_ids.ids for sheet in sheets]
        period_ids = list(itertools.chain.from_iterable(period_ids))
        if len(period_ids):
            self.env.cr.execute("""
                        SELECT
                               sum(total_attendance) as total_attendance,
                               sum(total_timesheet) as total_timesheet,
                               sum(total_difference) as  total_difference
                        FROM hr_timesheet_sheet_sheet_day
                        WHERE id IN %s
                    """, (tuple(period_ids),))
            data = self.env.cr.dictfetchall()
            for x in data:
                timesheet_hours = x.pop('total_timesheet')
                timesheet_attendance = x.pop('total_attendance')
                timesheet_difference = x.pop('total_difference')

        return {
            'timesheet_hours': timesheet_hours,
            'timesheet_attendance': timesheet_attendance,
            'timesheet_difference': timesheet_difference,
            'total_hours': total_hours,
        }

    @api.onchange('employee_id', 'date_from')
    def onchange_employee(self):
        super(HrPayslip, self).onchange_employee()
        if self.contract_id.timesheet_payroll:
            datas = self.compute_timesheet_hours(self.contract_id, self.date_from, self.date_to)
            self.timesheet_hours = datas.get('timesheet_hours') or 0.0
            self.total_hours = datas.get('total_hours') or 0.0
        return

    @api.model
    def get_payslip_lines(self, contract_ids, payslip_id):
        class BrowsableObject(object):
            def __init__(self, employee_id, dict):
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0
        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                                FROM hr_payslip as hp, hr_payslip_line as pl
                                WHERE hp.employee_id = %s AND hp.state = 'done'
                                AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0
            for record in self:
                timesheet_hours = record.timesheet_hours
                total_hours = record.total_hours
        return super(HrPayslip, self).get_payslip_lines(contract_ids, payslip_id)
