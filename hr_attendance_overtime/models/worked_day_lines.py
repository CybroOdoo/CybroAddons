# -*- coding: utf-8 -*-

from datetime import timedelta, datetime
from odoo import models, fields, api, _


class WorkedDayOvertime(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """

        def was_on_leave_interval(employee_id, date_from, date_to):
            date_from = fields.Datetime.to_string(date_from)
            date_to = fields.Datetime.to_string(date_to)
            return self.env['hr.holidays'].search([
                ('state', '=', 'validate'),
                ('employee_id', '=', employee_id),
                ('type', '=', 'remove'),
                ('date_from', '<=', date_from),
                ('date_to', '>=', date_to)
            ], limit=1)

        res = []
        normal_hours = 0
        total_hours = 0
        number_of_days = 0
        contract_id = []
        # fill only if the contract as a working schedule linked
        uom_day = self.env.ref('product.product_uom_day', raise_if_not_found=False)
        contract_id = []
        for contract in self.env['hr.contract'].browse(contract_ids).filtered(lambda contract: contract.working_hours):
            contract_val = contract
            uom_hour = contract.employee_id.resource_id.calendar_id.uom_id or self.env.ref('product.product_uom_hour',
                                                                                           raise_if_not_found=False)
            interval_data = []
            holidays = self.env['hr.holidays']
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }
            leaves = {}
            day_from = fields.Datetime.from_string(date_from)
            day_to = fields.Datetime.from_string(date_to)
            nb_of_days = (day_to - day_from).days + 1

            # Gather all intervals and holidays
            for day in range(0, nb_of_days):
                working_intervals_on_day = contract.working_hours.get_working_intervals_of_day(
                    start_dt=day_from + timedelta(days=day))
                for interval in working_intervals_on_day:
                    interval_data.append(
                        (interval, was_on_leave_interval(contract.employee_id.id, interval[0], interval[1])))

            # Extract information from previous data. A working interval is considered:
            # - as a leave if a hr.holiday completely covers the period
            # - as a working period instead
            for interval, holiday in interval_data:
                holidays |= holiday
                hours = (interval[1] - interval[0]).total_seconds() / 3600.0
                if holiday:
                    # if he was on leave, fill the leaves dict
                    if holiday.holiday_status_id.name in leaves:
                        leaves[holiday.holiday_status_id.name]['number_of_hours'] += hours
                    else:
                        leaves[holiday.holiday_status_id.name] = {
                            'name': holiday.holiday_status_id.name,
                            'sequence': 5,
                            'code': holiday.holiday_status_id.name,
                            'number_of_days': 0.0,
                            'number_of_hours': hours,
                            'contract_id': contract.id,
                        }
                else:
                    # add the input vals to tmp (increment if existing)
                    attendances['number_of_hours'] += hours

            # Clean-up the results
            leaves = [value for key, value in leaves.items()]
            for data in [attendances] + leaves:
                data['number_of_days'] = uom_hour._compute_quantity(data['number_of_hours'], uom_day) \
                    if uom_day and uom_hour \
                    else data['number_of_hours'] / 8.0
                if data['name'] == 'Normal Working Days paid at 100%':
                    number_of_days = data['number_of_days']
                    normal_hours = data['number_of_hours']
                    contract_id = data['contract_id']
                res.append(data)

        date_from = fields.Datetime.from_string(date_from)
        date_from += timedelta(days=-1)
        date_from = str(date_from)
        date_to = fields.Datetime.from_string(date_to)
        date_to += timedelta(days=1)
        date_to = str(date_to)
        for attn_lines in self.env['hr.attendance'].search([('check_in', '>=', date_from),
                                                            ('check_out', '<=', date_to),
                                                            ('employee_id', '=', contract_val.employee_id.id)]):
            check_in = datetime.strptime(attn_lines.check_in, '%Y-%m-%d %H:%M:%S')
            check_out = datetime.strptime(attn_lines.check_out, '%Y-%m-%d %H:%M:%S')
            time_diff = check_out - check_in
            total_hours += ((time_diff.seconds / 60) / 60)
        ovt_hours = total_hours - normal_hours

        if ovt_hours > 0:
            res.append({
                'code': 'OVT',
                'contract_id': contract_id,
                'number_of_days': number_of_days,
                'number_of_hours': ovt_hours,
                'name': 'Overtime Hours',
            })
        return res
