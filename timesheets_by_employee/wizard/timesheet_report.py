# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError


class TimesheetReport(models.TransientModel):
    """Create a Transient model for Wizard"""
    _name = 'timesheet.report'
    _description = 'Timesheet Report Wizard'

    user_id = fields.Many2one(
        'res.users',
        string="Employee",
        required=True,
        help="You can select the employee")
    from_date = fields.Date(
        string="Starting Date",
        help="You can select the starting dates for the PDF report")
    to_date = fields.Date(
        string="Ending Date",
        help="You can select the ending dates for the PDF report")

    def print_timesheet(self):
        """Redirects to the report with the values obtained from the wizard.

        Returns:
            dict: The report action dictionary with employee and date parameters.
        """
        today = fields.Date.context_today(self)
        if self.from_date and self.from_date > today:
            raise UserError(_("The start date cannot be in the future."))
        if self.to_date and self.to_date > today:
            raise UserError(_("The end date cannot be in the future."))
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise UserError(_("The start date cannot be after the end date."))
        data = {
            'employee': self.user_id.id,
            'start_date': self.from_date,
            'end_date': self.to_date,
        }
        return self.env.ref(
            'timesheets_by_employee.action_report_print_timesheets'
        ).report_action(self, data=data)
