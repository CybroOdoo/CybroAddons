# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Yadhu Shankar E (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class HrEmployee(models.Model):
    """ Inherited hr_employee model to add field Joining Date """
    _inherit = "hr.employee"

    @api.model
    def _cron_anniversary_reminder(self):
        """Send work anniversary wishes to employees."""
        today = fields.Date.today()

        for employee in self.search([]):
            start = employee.contract_date_start

            if not start:
                continue
            # Must be at least 1 full year old
            if start > today:
                continue
            # Check if today is an anniversary
            # Anniversary = same day & month
            if start.month == today.month and start.day == today.day:
                # Check completed years (> 0)
                years = relativedelta(today, start).years
                if years >= 1:
                    template = self.env.ref(
                        'work_anniversary_reminder.email_template_anniversary_reminder'
                    )
                    template.send_mail(employee.id, force_send=True)
