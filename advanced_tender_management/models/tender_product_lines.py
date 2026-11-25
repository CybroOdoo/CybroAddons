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


class TenderProductLines(models.Model):
    """Product, section or note line of a tender."""
    _name = "tender.product.lines"
    _description = 'Tender Product Lines'
    _order = 'sequence, id'

    name = fields.Char(string='Description', required=True,
                       help='Description of the product line.')
    tender_id = fields.Many2one('tender.management',
                                help='Tender the line belongs to.')
    product_id = fields.Many2one('product.product',
                                 help='Product requested in the tender.')
    product_code = fields.Char(string='Code', related='product_id.default_code',
                               help='Internal reference of the product.')
    product_qty = fields.Float(string='Qty', digits='Product Unit', default=1.0,
                               required=True,
                               help='Requested quantity, in the unit of measure of the product.')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure',
                                     related='product_id.uom_id',
                                     help='Unit of measure of the product.')
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False, help='Technical field for sections and notes.')
    sequence = fields.Integer(default=10, help='Order of the line in the tender.')

    _product_qty_positive = models.Constraint(
        'CHECK (display_type IS NOT NULL OR product_qty > 0)',
        'The quantity of a product line must be greater than zero.')

    def write(self, vals):
        """Carry a new quantity of a tender line to the bids still open,
        so that they keep pricing the quantity the tender asks for."""
        res = super().write(vals)
        if 'product_qty' in vals and self._name == 'tender.product.lines':
            bid_lines = self.env['tender.bidding.product.lines'].search([
                ('tender_line_id', 'in', self.ids),
                ('tender_bidding_id.bidding_state', 'not in', ('won', 'lost')),
            ])
            for line in self:
                bid_lines.filtered(lambda bid_line: bid_line.tender_line_id == line).write(
                    {'product_qty': line.product_qty})
        return res
