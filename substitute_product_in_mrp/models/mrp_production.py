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
from odoo import models


class MrpProduction(models.Model):
    """ Inherited MRP production to substitute unavailable components upon confirmation. """
    _inherit = 'mrp.production'

    def action_confirm(self):
        """ Confirm manufacturing order and substitute unavailable components with fallback products. """
        res = super().action_confirm()
        for production in self:
            for bom_line in production.bom_id.bom_line_ids.filtered(
                    lambda x: x.mrp_substitute_product_id):
                substitute = bom_line.mrp_substitute_product_id
                # Skip service-type products — they have no stock to substitute
                if substitute.type == 'service':
                    continue
                for move_raw_id in production.move_raw_ids:
                    # Use free_qty (on-hand minus reserved) to detect true
                    # out-of-stock, instead of qty_available which ignores
                    # reservations. Also allow storable products (type ==
                    # 'product'), not just consumables (type == 'consu').
                    if (move_raw_id.product_id.free_qty <= 0 and
                            move_raw_id.product_id == bom_line.product_id):
                        if substitute.free_qty >= move_raw_id.product_uom_qty:
                            move_raw_id.write({'product_id': substitute.id})
        return res
