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

from odoo import models, fields


class ProductStockLocation(models.Model):
    _inherit = "stock.quant"

    virtual_available = fields.Float('Forecasted Quantity',
                                     compute="_compute_location_qty")
    incoming_qty = fields.Float('Incoming', compute="_compute_location_qty")
    outgoing_qty = fields.Float('Outgoing', compute="_compute_location_qty")

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
