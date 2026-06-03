# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
from odoo import api, fields, models


class TenderBiddingProductLines(models.Model):
    """ Class for holding tender bidding product lines. """
    _name = "tender.bidding.product.lines"
    _inherit = 'tender.product.lines'
    _description = 'Tender Bidding Product Lines'

    tender_id = fields.Many2one('tender.management', related='tender_bidding_id.tender_id',help='related tender for '
                                                                                                'the bid')
    vendor_id = fields.Many2one('res.partner', related='tender_bidding_id.vendor_id',help='related vendor for the bid')
    bid_qualified = fields.Selection(
        [('initial', 'Initial'), ('qualified', 'Qualified'), ('disqualified', 'Disqualified')],
        related='tender_bidding_id.qualification_stage',help='has the bid qualified or not ?')
    tender_bidding_id = fields.Many2one('tender.bidding',help='related bid')
    product_price = fields.Float(string="Your Price", help="product price")
    product_total = fields.Float(string="Product Total", help="product price total", compute="_compute_product_total",
                                 store=True)
    bid_chosen = fields.Boolean(string="Purchase Bid", default=False,help='bid selected for the tender')
    bid_status = fields.Selection([('selected', 'Selected'), ('re_select', 'Re Select')],help='reselect the bid for '
                                                                                              'the tender')

    @api.depends('product_price')
    def _compute_product_total(self):
        """Function to compute total product price of each tender bidding product line"""
        for rec in self:
            rec.product_total = rec.product_qty * rec.product_price

    def action_confirm_bid(self):
        """Function to confirm selected product wise bids"""
        self.bid_chosen = True
        self.bid_status = 'selected'
        self.env['tender.bidding.product.lines'].search(
            [('product_id', '=', self.product_id.id), ('tender_id', '=', self.tender_id.id)]).filtered(
            lambda rec: rec.id != self.id).write({
            'bid_chosen': True,
            'bid_status': 're_select'
        })

    def action_reselect_bid(self):
        """Function to reselect product wise bid"""
        self.bid_status = 'selected'
        self.env['tender.bidding.product.lines'].search(
            [('product_id', '=', self.product_id.id), ('tender_id', '=', self.tender_id.id)]).filtered(
            lambda rec: rec.id != self.id).write({
            'bid_status': 're_select'
        })

    def action_selected_bid(self):
        """Function to select product wise bid"""
        return
