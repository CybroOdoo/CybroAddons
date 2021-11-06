# -*- coding: utf-8 -*-
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
        emp_obj = self.env['hr.employee'].search([])
        for each in emp_obj:
            each.write({'check_list_enable': enable_checklist})

