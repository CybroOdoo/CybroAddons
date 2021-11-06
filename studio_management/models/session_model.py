# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SessionDetails(models.Model):
    _name = 'session.details'

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    order_date = fields.Datetime(string='Order Date')
    return_date = fields.Datetime(string='Return Date')
    type_id = fields.Many2one('session.type', string='Type')
    editing_work_id = fields.One2many('editing.works', 'session_id', string='Editing Work')
    note_field = fields.Html(string='Comment')
    state = fields.Selection([('draft', 'Draft'), ('design', 'Designing'), ('closed', 'Closed')],
                             string='State', default='draft', required=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('session.details') or 'New'
        return super(SessionDetails, self).create(vals)

    @api.multi
    def submit_session(self):
        self.state = 'design'

    @api.multi
    def close_session(self):
        for rec in self.editing_work_id:
            if rec.state != 'completed':
                raise UserError(_('All Works Must Be Completed'))
        if self.return_date:
            self.state = 'closed'
        else:
            raise UserError(_('Please update your Return Date'))


class SessionType(models.Model):
    _name = 'session.type'

    name = fields.Char(string='Name')
