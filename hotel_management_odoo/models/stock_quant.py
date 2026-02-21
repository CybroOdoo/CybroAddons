# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ADARSH K (odoo@cybrosys.com)
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
from odoo import models, api, _
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    """Inherit Stock Quant to restrict Room Quantity Update"""
    _inherit = 'stock.quant'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to check for room products"""
        for vals in vals_list:
            if vals.get('product_id'):
                product = self.env['product.product'].browse(vals['product_id'])
                if product.is_room:
                     raise ValidationError(_("You cannot update the quantity of a Room product directly."))
        return super(StockQuant, self).create(vals_list)

    def write(self, vals):
        """Override write to check for room products"""
        if 'inventory_quantity' in vals or 'quantity' in vals:
            for record in self:
                if record.product_id.is_room:
                    raise ValidationError(_("You cannot update the quantity of a Room product directly."))
        return super(StockQuant, self).write(vals)
