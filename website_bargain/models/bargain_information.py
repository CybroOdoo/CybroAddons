# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class BargainInformation(models.Model):
    """Class for adding bidder details to the database"""
    _name = 'bargain.information'
    _rec_name = 'auction_id'
    _description = "Bidder Details"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    bidder_id = fields.Many2one('res.partner', string='Bidder', required=True,
                                help="Bidders details")
    auction_id = fields.Many2one('website.bargain', string='Auction',
                                 required=True, help="Auction Details")
    currency_id = fields.Many2one(related="auction_id.currency_id",
                                  help="Currency Details")
    bid_offer = fields.Monetary(string="Bid Offer",
                                currency_field='currency_id',
                                help="Offered amount")
    status = fields.Char(string="Status", readonly=True,
                         help="Current Status of bid")
    product_id = fields.Many2one(related='auction_id.product_id',
                                 string='Product', help="Product details")
