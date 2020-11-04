# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Ijaz Ahammed (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, api, fields


class PayslipLateCheckIn(models.Model):
    _inherit = 'hr.payslip'

    late_check_in_ids = fields.Many2many('late.check_in')

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        """
        function used for writing late check-in record in payslip
        input tree.

        """
        res = super(PayslipLateCheckIn, self).get_inputs(contracts, date_to, date_from)
        late_check_in_type = self.env.ref('employee_late_check_in.late_check_in')
        contract = self.contract_id
        late_check_in_id = self.env['late.check_in'].search([('employee_id', '=', self.employee_id.id),
                                                             ('date', '<=', self.date_to),
                                                             ('date', '>=', self.date_from),
                                                             ('state', '=', 'approved'),
                                                             ])
        amount = late_check_in_id.mapped('amount')
        cash_amount = sum(amount)
        if late_check_in_id:
            self.late_check_in_ids = late_check_in_id
            input_data = {
                'name': late_check_in_type.name,
                'code': late_check_in_type.code,
                'amount': cash_amount,
                'contract_id': contract.id,
            }
            res.append(input_data)
        return res

    def action_payslip_done(self):
        """
        function used for marking deducted Late check-in
        request.

        """
        for recd in self.late_check_in_ids:
            recd.state = 'deducted'
        return super(PayslipLateCheckIn, self).action_payslip_done()
