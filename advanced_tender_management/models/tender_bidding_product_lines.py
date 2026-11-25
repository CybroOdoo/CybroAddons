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
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class TenderBiddingProductLines(models.Model):
    """Price offered by a vendor for one line of a tender."""
    _name = "tender.bidding.product.lines"
    _inherit = 'tender.product.lines'
    _description = 'Tender Bidding Product Lines'

    tender_id = fields.Many2one('tender.management', related='tender_bidding_id.tender_id',
                                help='Tender of the bid.')
    vendor_id = fields.Many2one('res.partner', related='tender_bidding_id.vendor_id',
                                help='Vendor of the bid.')
    bid_qualified = fields.Selection(related='tender_bidding_id.qualification_stage',
                                     help='Qualification stage of the bid.')
    tender_bidding_id = fields.Many2one('tender.bidding', help='Bid the line belongs to.',
                                        ondelete='cascade', index=True)
    tender_line_id = fields.Many2one('tender.product.lines', ondelete='set null',
                                     index='btree_not_null',
                                     help='Tender line priced by this bid line.')
    product_price = fields.Float(string="Your Price", help="Unit price offered by the vendor.")
    product_total = fields.Float(help="Quantity multiplied by the offered price.",
                                 compute="_compute_product_total", store=True)
    bid_chosen = fields.Boolean(string="Purchase Bid", default=False,
                                help='A line of this product has been chosen for the tender.')
    bid_status = fields.Selection([('selected', 'Selected'), ('re_select', 'Re Select')],
                                  help='Whether this line is the one to purchase.')

    @api.depends('product_qty', 'product_price')
    def _compute_product_total(self):
        """Compute the total price of each bidding line."""
        for rec in self:
            rec.product_total = rec.product_qty * rec.product_price

    @api.constrains('product_qty', 'tender_line_id', 'display_type')
    def _check_quantity_matches_tender(self):
        """A bid prices the quantity asked by the tender; it cannot change it."""
        digits = self.env['decimal.precision'].precision_get('Product Unit')
        for line in self:
            if line.tender_line_id and not line.display_type and float_compare(
                    line.product_qty, line.tender_line_id.product_qty,
                    precision_digits=digits):
                raise ValidationError(self.env._(
                    'The quantity of "%(line)s" on bid %(bid)s must be %(qty)s, '
                    'the quantity asked by the tender.',
                    line=line.name, bid=line.tender_bidding_id.name,
                    qty=line.tender_line_id.product_qty))

    def _other_lines_of_product(self):
        """Lines of the other vendors for the same product and tender."""
        self.ensure_one()
        return self.search([
            ('product_id', '=', self.product_id.id),
            ('tender_id', '=', self.tender_id.id),
            ('id', '!=', self.id),
        ])

    def _check_tender_open_for_selection(self):
        """Lines are chosen while the tender is evaluated or selected."""
        if any(rec.tender_id.tender_state not in ('bid_evaluation', 'bid_selection')
               for rec in self):
            raise UserError(self.env._(
                'Bid lines can only be chosen while the tender is in Bid Evaluation or '
                'Bid Selection.'))

    def action_confirm_bid(self):
        """Choose this line for its product."""
        self._check_tender_open_for_selection()
        for rec in self:
            rec.write({'bid_chosen': True, 'bid_status': 'selected'})
            rec._other_lines_of_product().write({'bid_chosen': True, 'bid_status': 're_select'})

    def action_reselect_bid(self):
        """Choose this line instead of the line chosen before."""
        self._check_tender_open_for_selection()
        for rec in self:
            rec.bid_status = 'selected'
            rec._other_lines_of_product().write({'bid_status': 're_select'})

    def action_selected_bid(self):
        """Button showing that the line is selected; it does nothing."""
        return None
