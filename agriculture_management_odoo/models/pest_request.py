# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models, fields, api, _


class PestRequests(models.Model):
    _name = 'pest.request'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Pest Request'
    _rec_name = 'reference'

    reference = fields.Char(string='Reference', required=True, copy=False,
                            readonly=True, tracking=True,
                            default=lambda self: _('New'))
    request_date = fields.Date(string='Request Date',
                               default=fields.Date.context_today, required=True,
                               tracking=True)
    farmer_id = fields.Many2one('res.partner', string='Farmer', required=True,
                                tracking=True)
    crop_id = fields.Many2one('crop.requests', string='Crop', required=True,
                              tracking=True)
    location_id = fields.Many2one('location.details', string='Location',
                                  tracking=True)
    pest_id = fields.Many2one('pest.details', string='Pest', required=True,
                              tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda
                                      self: self.env.user.company_id.currency_id)
    pest_quantity = fields.Integer(string='Pest Quantity', required=True,
                                   tracking=True)
    pest_cost = fields.Float(string='Pest Cost', required=True,
                             tracking=True, related='pest_id.pest_cost')
    total_cost = fields.Float(string='Total Cost',
                              compute='_compute_total_cost', store=True,
                              tracking=True)
    disease = fields.Text(string='Disease', tracking=True, required=True)
    note = fields.Text(string='Note', tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('pending', 'Pending'), ('approve', 'Approved'),
         ('rejected', 'Rejected')],
        string='Status', default='draft', tracking=True)

    def action_draft(self):
        self.state = 'draft'

    def action_pending(self):
        self.state = 'pending'

    def action_approved(self):
        self.state = 'approve'

    def action_rejected(self):
        self.state = 'rejected'

    @api.depends('pest_cost', 'pest_quantity')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.pest_cost * record.pest_quantity

    @api.model
    def create(self, values):
        if values.get('reference', _('New')) == _('New'):
            values['reference'] = self.env['ir.sequence'].next_by_code(
                'pest.request') or _('New')
        res = super(PestRequests, self).create(values)
        return res
