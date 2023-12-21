# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: JANISH BABU  (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models

"""Inherited hr.employee to add field Joining Date"""


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    joining_date = fields.Date(string='Joining Date',
                               help="Employee joining date",
                               compute='_compute_joining_date')

    @api.depends('contract_id')
    def _compute_joining_date(self):
        """ Methode for computing the Joining date from Contract """
        for rec in self:
            rec.joining_date = min(rec.contract_id.mapped('date_start')) \
                if rec.contract_id else False

    @api.model
    def _cron_anniversary_reminder(self):
        """Sending wishes email to employees"""
        for employee in self.search([]):
            today_month = fields.Date.today().month
            today_day = fields.Date.today().day
            if employee.joining_date and \
                    employee.joining_date.day == today_day and \
                    employee.joining_date.month == today_month:
                mail_template = self.env.ref(
                    'work_anniversary_reminder.email_template_anniversary_reminder')
                mail_template.send_mail(employee.id, force_send=True)
