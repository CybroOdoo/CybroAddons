# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhammed Dilshad Tk (odoo@cybrosys.com)
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
import calendar

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrEmployee(models.Model):
    """ Inherited hr_employee model to add field Joining Date """
    _inherit = "hr.employee"

    @api.model
    def _cron_anniversary_reminder(self):
        """Send work anniversary wishes to employees."""
        today = fields.Date.today()
        template = self.env.ref(
            'work_anniversary_reminder.email_template_anniversary_reminder',
            raise_if_not_found=False,
        )
        if not template:
            return
        employees = self.search([('contract_date_start', '!=', False)])
        for employee in employees:
            start = employee.contract_date_start
            if start > today:
                continue
            is_anniversary = (
                start.month == today.month and start.day == today.day
            )
            # Employees hired on February 29 are wished on February 28
            # during non-leap years.
            if (not is_anniversary
                    and start.month == 2 and start.day == 29
                    and today.month == 2 and today.day == 28
                    and not calendar.isleap(today.year)):
                is_anniversary = True
            if is_anniversary and relativedelta(today, start).years >= 1:
                template.send_mail(employee.id, force_send=True)
