# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class EditingWorks(models.Model):
    _name = 'editing.works'

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    session_id = fields.Many2one('session.details', string='Session Id')
    work_done = fields.Char(string='Work', required=True)
    time_taken = fields.Float(string='Time Taken', required=True)
    work_by = fields.Many2one('res.users', string='Work By', required=True, default=lambda self: self.env.user)
    state = fields.Selection([('draft', 'Draft'), ('ongoing', 'Ongoing'), ('completed', 'Completed')],
                             string='State', default='draft', required=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('editing.works') or 'New'
        return super(EditingWorks, self).create(vals)
