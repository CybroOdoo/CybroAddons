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
from odoo import api, fields, models


class CalendarLeave(models.TransientModel):
    """Transient model for showing the values in hr holiday generator wizard"""
    _name = 'calendar.leave'
    _description = 'Calendar Leave'

    holiday_generator_id = fields.Many2one('hr.holiday.generator',
                                           string='Holiday Generator',
                                           help="A Many2one field to connect to"
                                                "the model hr_holiday_generator"
                                           )
    name = fields.Char(string="Name", help="name of the public holiday")
    start_date = fields.Datetime(string="Start Date",
                                 help="Start date of the public holiday")
    end_date = fields.Datetime(string="End Date",
                               help="End date of the public holiday")
    description = fields.Char(string="Description",
                              help="Description of the public holiday")
    warning = fields.Boolean(string="Warning",
                             help="Warning to show holidays of same dates",
                             compute="compute_warning", default=False)
    calendar_leave_generator_id = fields.Many2one(
        "calendar.leave.generator",
        string="Calendar leave generator",
        help="For connecting with calendar leave generator")

    @api.depends('start_date')
    def compute_warning(self):
        """Compute function for the boolean warning"""
        for record in self:
            same_date_records = self.filtered(
                lambda dates: dates.start_date == record.start_date and
                dates.id != record.id)
            for dates in same_date_records:
                dates.warning = True
            record.warning = bool(same_date_records)
