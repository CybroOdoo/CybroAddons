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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    @api.model
    def get_available_lots_for_pos(self, product_id, company_id=None, config_id=None, used_lots=None):
        """Get available lots for a product suitable for the Point of Sale (PoS).
        Filters by company and PoS configuration source location in the database,
        prioritizing lots expiring soonest, while excluding lots already used in draft orders."""
        company_id = company_id or self.env.company.id
        location_ids = []
        if config_id:
            pos_config = self.env['pos.config'].browse(config_id)
            src_loc = pos_config.picking_type_id.default_location_src_id
            if src_loc:
                location_ids = src_loc.child_internal_location_ids.ids

        domain = [
            ('product_id', '=', product_id),
            ('lot_id', '!=', False),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', company_id),
        ]
        if location_ids:
            domain.append(('location_id', 'in', location_ids))
        else:
            domain.append(('location_id.usage', '=', 'internal'))

        if used_lots:
            domain.append(('lot_id.name', 'not in', used_lots))

        quants = self.env['stock.quant']._read_group(
            domain=domain,
            groupby=['lot_id'],
            aggregates=['quantity:sum'],
            having=[('quantity:sum', '>', 0)],
        )
        lot_ids = [lot.id for lot, _sum in quants if lot]
        if not lot_ids:
            return []

        lot_domain = [('id', 'in', lot_ids)]
        if used_lots:
            lot_domain.append(('name', 'not in', used_lots))

        lots = self.search(lot_domain, order='expiration_date asc, create_date asc')

        return lots[:1].mapped('name')
