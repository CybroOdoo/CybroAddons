# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Nilmar Shereef (<https://www.cybrosys.com>)
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
from odoo import models, fields, api


class MenuThemes(models.Model):
    _name = 'hr.settings'
    _inherit = 'res.config.settings'

    enable_checklist = fields.Boolean(string='Enable Checklist Progress in Kanban?')

    @api.multi
    def set_enable_checklist(self):
        ir_values = self.env['ir.values']
        enable_checklist = self.enable_checklist
        ir_values.set_default('hr.settings', 'enable_checklist', enable_checklist)
        emp_obj = self.env['hr.employee'].sudo().search([])
        for each in emp_obj:
            each.write({'check_list_enable': enable_checklist})

