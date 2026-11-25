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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


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

    @api.depends('product_id', 'location_id', 'company_id')
    def _compute_location_qty(self):
        """Method to compute the quantity of incoming and outgoing stock."""
        for rec in self:
            if rec.product_id and rec.location_id:
                ctx = {'location': rec.location_id.id}
                if rec.company_id:
                    ctx['company_id'] = rec.company_id.id
                    ctx['allowed_company_ids'] = [rec.company_id.id]
                product = rec.product_id.with_context(**ctx)
                rec.virtual_available = product.virtual_available
                rec.incoming_qty = product.incoming_qty
                rec.outgoing_qty = product.outgoing_qty
            else:
                rec.virtual_available = 0.0
                rec.incoming_qty = 0.0
                rec.outgoing_qty = 0.0
