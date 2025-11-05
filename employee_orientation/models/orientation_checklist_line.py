# -*- coding: utf-8 -*-

from odoo import models, fields


class ChecklistLine(models.Model):
    _name = 'checklist.line'
    _rec_name = 'line_name'

    line_name = fields.Char(string='Name', required=True)
    responsible_user = fields.Many2one('res.users', string='Responsible User', required=True)
