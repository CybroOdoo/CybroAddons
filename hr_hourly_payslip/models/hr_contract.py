# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    """Class for the inherited model hr_contact"""
    _inherit = 'hr.contract'

    hourly_payslip = fields.Boolean(help='Enable to see the hours spend by the'
                                         ' employee in the payslip.',
                                    string='Hourly Payslip')
    hourly_wage = fields.Monetary(string='Hourly Wage', help='Wage per hour for the '
                                                      'employee')

    @api.onchange('hourly_payslip')
    def _onchange_hourly_payslip(self):
        """This method will work when the user modifies the hourly_payslip
           field. According to the conditions, will add a new python code to
           the Basic salary rule."""
        if self.hourly_payslip is True:
            rule_id = self.env['hr.salary.rule'].browse(
                self.env.ref('hr_payroll_community.hr_rule_basic').id)
            rule_id.write({
                'amount_python_compute': 'result = contract.hourly_wage*payslip.total_hours'
            })

    @api.constrains('hourly_wage')
    def _check_hourly_wage(self):
        """Method to add constraints for the hourly_wage field, as it
        should be a positive value."""
        if self.hourly_payslip is True and self.hourly_wage <= 0:
            raise ValidationError(_('Wage should be a positive value.'))
