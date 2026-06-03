# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)

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


class TenderProductLines(models.Model):
    """ Class for holding tender product lines. """
    _name = "tender.product.lines"
    _description = 'Tender Product Lines'

    name = fields.Char(string='Description',required=True,help='product description')
    tender_id = fields.Many2one('tender.management',help='related tender')
    product_id = fields.Many2one('product.product', string='Product',help='tender product for bidding')
    product_code = fields.Char(string='Code', related='product_id.default_code',help='product code')
    product_qty = fields.Integer(string='Qty',default=1,help='product quantity')
    product_uom_id = fields.Many2one('uom.uom',string='Unit of Measure', related='product_id.uom_id',help='product '
                                                                                                          'unit of '
                                                                                                          'measure')
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False,help='display type for the product lines')
    sequence = fields.Integer(string='Sequence',help='sequence for the tender product line')
