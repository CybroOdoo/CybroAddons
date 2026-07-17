# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Busthana Shirin (odoo@cybrosys.com)
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
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hourly_payslip = fields.Boolean(help='Enable to see the hours spend by the'
                                         ' employee in the payslip.',
                                    string='Hourly Payslip')

    @api.onchange('hourly_payslip')
    def _onchange_hourly_payslip(self):
        """ This method will work when the user modifies the Hourly Cost
        field. According to the conditions, will add a new python code to
        the Basic salary rule. """
        if self.hourly_payslip:
            rule_id = self.env['hr.salary.rule'].browse(
                self.env.ref('hr_payroll_community.hr_rule_basic').id)
            rule_id.write({
                'amount_python_compute': 'result = employee.hourly_cost*payslip.total_hours'
            })
