# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import fields, models
from odoo.exceptions import UserError


class BidSelection(models.TransientModel):
    """Select or change the final bid of a single vendor tender."""
    _name = "bid.selection"
    _description = 'Bid Selection'

    current_tender_id = fields.Many2one('tender.management', help='Tender of the bid.')
    tender_bid_id = fields.Many2one('tender.bidding', string='Bids',
                                    domain="[('tender_id', '=', current_tender_id)]",
                                    help='Bid to purchase.')
    vendor_id = fields.Many2one('res.partner', string="Vendor", related='tender_bid_id.vendor_id',
                                help='Vendor of the bid.')

    def action_confirm_purchase(self):
        """Create and confirm the purchase order of the chosen bid, mark the
        other bids of the tender as lost and close the tender."""
        self.ensure_one()
        tender = self.current_tender_id
        tender._check_tender_state(['bid_selection'])
        if not self.tender_bid_id:
            raise UserError(self.env._('Select the bid to purchase.'))
        if self.tender_bid_id.tender_id != tender:
            raise UserError(self.env._(
                'Bid %(bid)s does not belong to tender %(tender)s.',
                bid=self.tender_bid_id.name, tender=tender.name))
        if not self.vendor_id:
            raise UserError(self.env._(
                'Bid %s has no vendor; set one before confirming the purchase.',
                self.tender_bid_id.name))
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor_id.id,
            'partner_ref': self.tender_bid_id.name,
            'date_order': fields.Datetime.now(),
            'tender_id': tender.id,
            'order_line': [fields.Command.create({
                'product_id': False if line.display_type else line.product_id.id,
                'product_qty': 0 if line.display_type else line.product_qty,
                'price_unit': 0 if line.display_type else line.product_price,
                'name': line.name,
                'display_type': line.display_type,
            }) for line in self.tender_bid_id.tender_bid_products_ids],
        })
        purchase_order.button_confirm()
        template = self.env.ref('advanced_tender_management.purchase_order_confirmed_template').sudo()
        template.send_mail(purchase_order.id, force_send=True)
        tender.write({
            'purchase_confirmed': True,
            'tender_state': 'close',
            'purchase_order_ids': [fields.Command.link(purchase_order.id)],
        })
        self.tender_bid_id.bidding_state = 'won'
        self.env['tender.bidding'].search([
            ('tender_id', '=', tender.id), ('id', '!=', self.tender_bid_id.id),
        ]).write({'bidding_state': 'lost'})
