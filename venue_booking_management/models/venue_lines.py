# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class VenueLines(models.Model):
    """Model for managing the Venue lines"""
    _name = 'venue.lines'
    _description = 'Venue Lines'

    venue_id = fields.Many2one('venue', string='Venue Lines',
                               help='The relational field for the venue model')
    amenities_id = fields.Many2one('amenities', string='Amenities',
                                   help='The field used to link the '
                                        'amenities model')
    quantity = fields.Float(string="Quantity", default=1,
                            help="Quantity of the Amenities")
    amount = fields.Float(string="Amount", help="Amount of the Amenities",
                          related='amenities_id.amount')
    sub_total = fields.Float(string="Subtotal", compute="_compute_sub_total",
                             readonly=True, help="Sub Total of the Values")
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  string='Currency',
                                  default=lambda self:
                                  self.env.user.company_id.currency_id,
                                  help="Currency value of the Venue")
    status = fields.Selection([('open', 'Open'), ('done', 'Done')],
                              string="Status", default='open',
                              help="Status of the Venue")

    @api.depends('quantity', 'amount')
    def _compute_sub_total(self):
        """Compute the Sub Total of the Venue values"""
        for item in self:
            item.sub_total = item.quantity * item.amount
