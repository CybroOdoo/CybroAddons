# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from datetime import datetime
from odoo import Command, fields, models


class BidSelection(models.TransientModel):
    """Select or change the final bid for purchase order"""
    _name = "bid.selection"
    _description = 'Bid Selection'

    current_tender_id = fields.Many2one('tender.management',help='related tender')
    tender_bid_id = fields.Many2one('tender.bidding', string='Bids', domain="[('tender_id', '=', "
                                                                            "current_tender_id)]",help='related '
                                                                                                       'tender bid')
    vendor_id = fields.Many2one('res.partner', string="Vendor", related='tender_bid_id.vendor_id',help='related vendor')

    def action_confirm_purchase(self):
        """Function for confirming purchase order"""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor_id.id,
            'partner_ref': self.tender_bid_id.name,
            'date_order': datetime.today().now(),
            'order_line': [Command.create({
                'product_id': False if rec.display_type else rec.product_id.id,
                'product_qty': False if rec.display_type else rec.product_qty,
                'price_unit': False if rec.display_type else rec.product_price,
                'name': rec.name,
                'display_type': rec.display_type
            }) for rec in self.tender_bid_id.tender_bid_products_ids]
        })
        purchase_order.tender_id = self.current_tender_id.id
        purchase_order.button_confirm()
        template = self.env.ref('advanced_tender_management.purchase_order_confirmed_template').sudo()
        template.send_mail(purchase_order.id, force_send=True)
        self.current_tender_id.purchase_confirmed = True
        self.current_tender_id.update({'purchase_order_ids': [(fields.Command.link(purchase_order.id))]})
        self.tender_bid_id.bidding_state = 'won'
        self.env['tender.bidding'].search([]).filtered(
            lambda rec: rec.tender_id.id == self.current_tender_id.id and rec.id != self.tender_bid_id.id).write({
            'bidding_state': 'lost'
        })
