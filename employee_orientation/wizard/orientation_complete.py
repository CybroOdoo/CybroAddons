# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class OrientationForceComplete(models.TransientModel):
    _name = 'orientation.force.complete'

    name = fields.Char()
    orientation_id = fields.Many2one('employee.orientation', string='Orientation')
    orientation_lines = fields.One2many('orientation.request', string='Orientation Lines', compute='pending_lines')

    @api.onchange('orientation_id')
    def pending_lines(self):
        pending = []

        for data in self.orientation_id.orientation_request:
            if data.state == 'new':
                pending.append(data.id)
        self.update({'orientation_lines': pending})

    @api.multi
    def force_complete(self):
        for line in self.orientation_lines:
            if line.state != 'cancel':
                line.state = 'complete'
        self.orientation_id.write({'state': 'complete'})



