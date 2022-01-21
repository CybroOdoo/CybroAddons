# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api


class ProductStockLocation(models.Model):
    _inherit = "stock.quant"

    virtual_available = fields.Float(
        'Forecasted Quantity',
        compute="_compute_location_qty",
        readonly=True, required=True)
    incoming_qty = fields.Float(
        'Incoming',
        compute="_compute_location_qty",
        readonly=True, required=True)
    outgoing_qty = fields.Float(
        'Outgoing',
        compute="_compute_location_qty",
        readonly=True, required=True)

    def _compute_location_qty(self):
        for rec in self:
            product = self.env['product.product'].browse(rec.product_id.id)
            virtual_available = product.with_context({'location': rec.location_id.id}).virtual_available
            incoming_qty = product.with_context({'location': rec.location_id.id}).incoming_qty
            outgoing_qty = product.with_context({'location': rec.location_id.id}).outgoing_qty
            rec.virtual_available = virtual_available
            rec.incoming_qty = incoming_qty
            rec.outgoing_qty = outgoing_qty
