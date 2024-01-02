# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohamed Muzammil VP(<https://www.cybrosys.com>)
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


class SaleOrder(models.Model):
    """Inherit the sale.order model to add fields and functions"""
    _inherit = 'sale.order'

    quotation_ref = fields.Char(string='Quotation Reference',
                                copy=False, readonly=True, tracking=True,
                                help="Quotation reference number")

    @api.model
    def create(self, vals):
        """Method for generating sequence for quotation """
        res = super(SaleOrder, self).create(vals)
        seq_val = self.env.ref(
            'separate_quotation_number_odoo.seq_quotation').id
        res.quotation_ref = self.env['ir.sequence'].browse(
            seq_val).next_by_id()
        return res
