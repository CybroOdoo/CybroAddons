# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ruksana P  (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, models


class HrPayslip(models.Model):
    """ This class is used to create the bonus reasons. """
    _inherit = "hr.payslip"

    @api.onchange('employee_id', 'date_from', 'date_to')
    def _onchange_employee_id(self):
        """ When changing employee the bonus amount for the employee will be
        loaded as other input  """
        bonus_rule = self.env.ref(
            'employee_bonus_manager.hr_salary_rule_bonus')
        if bonus_rule.struct_id == self.struct_id:
            bonus = self.env['bonus.request'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'accounting'), ('move_id.state', '=', 'posted'),
                ('move_id.date', '>=', self.date_from),
                ('move_id.date', '<=', self.date_to)])
            amount = sum(bonus.mapped('bonus_amount'))
            self.input_line_ids = [(0, 0, {
                'input_type_id': self.env.ref(
                    'employee_bonus_manager.hr_payslip_input_type_bonus'),
                'amount': amount,
            })]
