# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
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
from odoo import api, models


class HrPayslip(models.Model):
    """Class for HR Payslip"""
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        """Calculate additional inputs for the employee payslip"""
        res = super().get_inputs(contracts, date_from, date_to)

        for contract in contracts:
            employee = contract.employee_id
            amount_employee = 0.0

            pantry_lines = self.env['pantry.order'].search([
                ('partner_id', '=', employee.user_id.partner_id.id)
            ])

            for order in pantry_lines:
                if date_from <= order.date_order.date() <= date_to:
                    amount_employee += order.amount_total

            for line in res:
                if line.get('code') == 'PR':
                    line['amount'] = line.get('amount', 0.0) + amount_employee

        return res
