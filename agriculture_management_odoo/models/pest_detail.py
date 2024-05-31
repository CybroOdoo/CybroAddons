# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav AR(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class PestDetail(models.Model):
    """ This model represents comprehensive details about pests within the
    context of agriculture management. """
    _name = 'pest.detail'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Pest Details In Agriculture Management'
    _rec_name = 'pest_name'

    pest_name = fields.Char(string='Pesticide', tracking=True,
                            help="Mention the pesticide name", required=True)
    pest_expiry_date = fields.Date(string='Expiry Date',
                                   help=" Mention the pesticide expiry date",
                                   required=True, tracking=True)
    pest_description = fields.Text(string='Pest Description', tracking=True,
                                   help="Brief description about the pesticide")
    pest_image = fields.Binary(string='Image', tracking=True,
                               help="Upload the image of pesticide")
    pest_cost = fields.Float(string='Cost', help="The cost of the pesticide",
                             required=True, tracking=True)
    pest_quantity = fields.Integer(string='Quantity',
                                   help="The quantity of pesticide purchased",
                                   required=True, tracking=True)
    total_cost = fields.Float(string='Total Cost', tracking=True,
                              help="The total cost of pesticide",
                              compute='_compute_total_cost', store=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, help='The company associated with the current user or '
        'environment.', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',
                                  help="Currency of company", string='Currency',
                                  default=lambda
                                  self: self.env.user.company_id.currency_id,
                                  tracking=True)

    @api.depends('pest_cost', 'pest_quantity')
    def _compute_total_cost(self):
        """Function for calculate total cost of pesticide """
        for record in self:
            record.total_cost = record.pest_cost * record.pest_quantity
