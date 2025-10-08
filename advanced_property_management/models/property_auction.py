# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyAuction(models.Model):
    """A class to represent the model property auction"""
    _name = 'property.auction'
    _description = 'Property Auction'
    _rec_name = 'auction_seq'

    auction_seq = fields.Char(string='Reference', readonly=True,
                              required=True, copy=False, default='New')
    property_id = fields.Many2one(
        'property.property', required=True,
        string='Property',
        domain="[('state','=','available'), ('sale_rent','=','for_auction')]",
        help='Related property for auction')
    responsible_id = fields.Many2one('res.users', required=True,
                                     string='Responsible User',
                                     help='The responsible person for '
                                          'managing the auction')
    bid_start_price = fields.Monetary(string='Bid Start Price',
                                      help='The starting bid price for '
                                           'the property')
    final_price = fields.Monetary(string='Final Price', readonly=True,
                                  help='The final price of the property')
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('started', 'Started'),
        ('ended', 'Ended'),
        ('canceled', 'Canceled')
    ], default='draft', string='State',
        help="* The \'Draft\' status is used when the auction is at draft.\n"
             "* The \'Confirmed\'status is used when the auction is confirmed\n"
             "* The \'Started\' status is used when the auction is started.\n"
             "* The \'Ended\' status is used when the auction is ended.\n"
             "* The \'Cancelled\' status is used when user cancel the auction.")
    participant_ids = fields.One2many('property.auction.line',
                                      'auction_id',
                                      string='Participants')
    start_time = fields.Datetime(string='Start Time',
                                 help='The starting time of the auction',
                                 required=True)
    end_time = fields.Datetime(string='End time',
                               help='The ending time of the auction',
                               required=True)
    auction_winner_id = fields.Many2one('res.partner',
                                        readonly=True,
                                        string='Auction Winner',
                                        help='The winner of the auction is '
                                             'selected according to the bids')
    sold = fields.Boolean(string='Sold', default=False,
                          help='Whether the property is sold or not')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  related='company_id.currency_id',
                                  required=True)

    @api.model
    def create(self, vals):
        """Supering the create function inorder to set the auction_seq number
        """
        if vals.get('auction_seq', 'New') == 'New':
            vals['auction_seq'] = self.env['ir.sequence'].next_by_code(
                'property.auction') or 'New'
        res = super(PropertyAuction, self).create(vals)
        return res

    @api.constrains('start_time','end_time')
    def check_start_time_end_time(self):
        current_date_time = datetime.now()
        if (not self.start_time > current_date_time < self.end_time or
                not self.start_time < self.end_time):
            raise ValidationError(_('Please provide a valid date and time'))

    def action_confirm(self):
        """Changes state to confirmed"""
        self.state = 'confirmed'

    def action_start(self):
        """Changes state to started"""
        self.state = 'started'

    def action_end(self):
        """Set state to ended and set values to fields auction_winner_id,
        final_price, end_time"""
        selected_line = \
            sorted(self.participant_ids, key=lambda x: x.bid_amount,
                   reverse=True)[
                0]
        self.auction_winner_id = selected_line.partner_id.id
        self.final_price = selected_line.bid_amount
        self.end_time = fields.Datetime.now()
        self.state = 'ended'

    def action_cancel(self):
        """Changes state to canceled"""
        self.state = 'canceled'

    def action_create_sale_order(self):
        """Creates a property sale record"""
        self.env['property.sale'].create({
            'property_id': self.property_id.id,
            'partner_id': self.auction_winner_id.id,
            'order_date': fields.Date.today(),
            'sale_price': self.final_price,
        })
        self.sold = True

    def action_view_sale_order(self):
        """View all the property sale from the auction"""
        return {
            'name': 'Property Sale: ' + self.auction_seq,
            'view_mode': 'tree,form',
            'res_model': 'property.sale',
            'type': 'ir.actions.act_window',
            'domain': [('property_id', '=', self.property_id.id)]
        }
