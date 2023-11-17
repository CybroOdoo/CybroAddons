# -*- coding: utf-8 -*-
###############################################################################
#
#  Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#  Author: Anusha C (odoo@cybrosys.com)
#
#  You can modify it under the terms of the GNU LESSER
#  GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#  You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#  (LGPL v3) along with this program.
#  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class CalendarLeaveGenerator(models.TransientModel):
    """Transient model for showing repeated calendar leaves"""
    _name = 'calendar.leave.generator'
    _description = 'Calendar Leave Generator'

    calendar_leave_ids = fields.One2many('calendar.leave',
                                         'calendar_leave_generator_id',
                                         string='Calender Leave',
                                         help="A One2many field to connect to"
                                              "the model calender leave")

    def action_generate(self):
        """Function for generating public holidays or showing the warning"""
        existing_holiday = self.env['resource.calendar.leaves'].search([
            ('resource_id', '=', False)])
        overlapping_dates = []
        overlapping_logs = []
        new_holiday_dates = []
        same_date_holidays = set()
        for existing in existing_holiday:
            for new_holiday in self.calendar_leave_ids:
                if existing.date_from.date() == \
                        new_holiday.start_date.date() or \
                        existing.date_to.date() == new_holiday.end_date.date():
                    overlapping_dates.append(new_holiday.start_date.date())
                    overlapping_logs.append({
                        'name': new_holiday.name,
                        'start_date': new_holiday.start_date,
                        'end_date': new_holiday.end_date,
                        'description': new_holiday.description
                    })
                    break
        for new_holiday in self.calendar_leave_ids:
            new_date = new_holiday.start_date.date()
            if new_date in new_holiday_dates:
                same_date_holidays.add(new_date)
            else:
                new_holiday_dates.append(new_date)
        for log in overlapping_logs:
            existing_logs = self.env['holiday.log'].search([
                ('name', '=', log['name']),
                ('start_date', '>=', log['start_date']),
                ('end_date', '<=', log['end_date'])])
            if not existing_logs:
                self.env['holiday.log'].create(log)
        if overlapping_dates or same_date_holidays:
            warning_message = ""
            if overlapping_dates:
                existing_dates = ", ".join(
                    date.strftime('%Y-%m-%d') for date in overlapping_dates)
                warning_message += (
                    f"Public holidays already exist for the following date(s): "
                    f"{existing_dates}.\nPlease refer to the logs for detailed "
                    f"information about the public holidays on these dates.\n\n"
                )
            if same_date_holidays:
                warning_message += "Select only one holiday per date:\n"
                warning_message += \
                    "The following dates have multiple holidays:\n"
            for date in same_date_holidays:
                warning_message += f"\n- {date.strftime('%Y-%m-%d')}"
            warning = self.env['overlapping.date'].create(
                {'warning': warning_message})
            return {
                'name': 'Overlapping Dates Warning',
                'type': 'ir.actions.act_window',
                'res_model': 'overlapping.date',
                'res_id': warning.id,
                'view_mode': 'form',
                'view_id': self.env.ref(
                    'hr_holiday_generator.overlapping_date_view_form').id,
                'target': 'new',
                'context': {
                    'active_calendar_leave_ids': self.calendar_leave_ids.ids
                }
            }
        else:
            self.env['resource.calendar.leaves'].create([{
                'name': holiday.name,
                'date_from': holiday.start_date,
                'date_to': holiday.end_date
            } for holiday in self.calendar_leave_ids])
