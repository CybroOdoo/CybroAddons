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

from odoo import models, fields


class LateCheckinSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    deduction_amount = fields.Float(string="Deduction Amount",
                                    config_parameter='employee_late_check_in.deduction_amount')
    maximum_minutes = fields.Char(string="Maximum Late Minute",
                                  config_parameter='employee_late_check_in.maximum_minutes')
    late_check_in_after = fields.Char(string="Late Check-in Starts After",
                                      config_parameter='employee_late_check_in.late_check_in_after')
    unpaid_leave = fields.Boolean(string="Unpaid Leave",
                                      config_parameter='employee_late_check_in.unpaid_leave')
    deduction_type = fields.Selection([('minutes', 'Per Minutes'), ('total', 'Per Total')],
                                  config_parameter='employee_late_check_in.deduction_type', default="minutes")

    def set_values(self):
        res = super(LateCheckinSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('deduction_amount', self.deduction_amount)
        self.env['ir.config_parameter'].sudo().set_param('maximum_minutes', self.maximum_minutes)
        self.env['ir.config_parameter'].sudo().set_param('late_check_in_after', self.late_check_in_after)
        self.env['ir.config_parameter'].sudo().set_param('unpaid_leave', self.unpaid_leave)
        self.env['ir.config_parameter'].sudo().set_param('deduction_type', self.deduction_type)
        return res
