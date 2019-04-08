# -*- coding: utf-8 -*-

from odoo import models, fields, _


class OrientationChecklist(models.Model):
    _name = 'orientation.checklist'
    _description = "Checklist"
    _rec_name = 'checklist_name'
    _inherit = 'mail.thread'

    checklist_name = fields.Char(string='Name', required=True)
    checklist_department = fields.Many2one('hr.department', string='Department', required=True)
    active = fields.Boolean(string='Active', default=True,
                            help="Set active to false to hide the Orientation Checklist without removing it.")
    checklist_line_id = fields.Many2many('checklist.line', 'checklist_line_rel', String="Checklist")







