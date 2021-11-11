# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
#############################################################################

from odoo import models, fields, api


class HRSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_checklist = fields.Boolean(string='Enable Checklist Progress in Kanban?', default=False)

    @api.model
    def get_values(self):
        res = super(HRSettings, self).get_values()
        config = self.env['ir.config_parameter'].sudo()
        enable_checklist = config.get_param('employee_check_list.enable_checklist', default=False)
        res.update(
            enable_checklist=enable_checklist
        )
        return res

    def set_values(self):
        super(HRSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('employee_check_list.enable_checklist',
                                                         self.enable_checklist)
        emp_obj = self.env['hr.employee'].search([])
        for rec in emp_obj:
            rec.write({'check_list_enable': self.enable_checklist})


