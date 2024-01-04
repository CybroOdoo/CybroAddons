# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
from odoo import models, fields


class StockQuant(models.Model):
    """Inherits model "stock.quant" and adds fields required"""
    _inherit = "stock.quant"

    virtual_available = fields.Float(string='Forecasted Quantity',
                                     compute="_compute_location_qty",
                                     help="Forecasted quantity of product.")
    incoming_qty = fields.Float(string='Incoming',
                                compute="_compute_location_qty",
                                help="Incoming quantity of product.")
    outgoing_qty = fields.Float(string='Outgoing',
                                compute="_compute_location_qty",
                                help="Outgoing quantity of product.")

    def _compute_location_qty(self):
        """Method to compute the quantity of incoming and outgoing stock."""
        for rec in self:
            product = rec.product_id
            rec.virtual_available = product.with_context(
                {'location': rec.location_id.id}).virtual_available
            rec.incoming_qty = product.with_context(
                {'location': rec.location_id.id}).incoming_qty
            rec.outgoing_qty = product.with_context(
                {'location': rec.location_id.id}).outgoing_qty
