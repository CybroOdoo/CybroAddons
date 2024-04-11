# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
        """This function calculates the additional inputs
         for the employee payslip."""
        res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        amount_employee = 0
        employee_id = self.env['hr.contract'].browse(
            contracts.id).employee_id
        pantry_lines = self.env['pantry.order'].search([
            ('partner_id', '=', employee_id.user_id.partner_id.id)
        ])
        for adv_obj in pantry_lines:
            if self.date_from <= adv_obj.date_order.date() <= self.date_to:
                amount_employee += adv_obj.amount_total
                for result in res:
                    result['amount'] = amount_employee
        return res
