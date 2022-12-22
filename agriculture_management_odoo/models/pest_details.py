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
from odoo import models, fields, api


class PestDetails(models.Model):
    _name = 'pest.details'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Pest Details'
    _rec_name = 'pest_name'

    pest_name = fields.Char(string='Pesticide', required=True, tracking=True)
    pest_expiry_date = fields.Date(string='Expiry Date', required=True,
                                   tracking=True)
    pest_description = fields.Text(string='Pest Description', tracking=True)
    pest_image = fields.Binary(string='Image', tracking=True)
    pest_cost = fields.Float(string='Cost', required=True, tracking=True)
    pest_quantity = fields.Integer(string='Quantity', required=True,
                                   tracking=True)
    total_cost = fields.Float(string='Total Cost',
                              compute='_compute_total_cost', store=True,
                              tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda
                                      self: self.env.user.company_id.currency_id,
                                  tracking=True)

    @api.depends('pest_cost', 'pest_quantity')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.pest_cost * record.pest_quantity
