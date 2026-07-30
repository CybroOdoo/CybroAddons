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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _process_order(self, order, draft, existing_order):
        """Override _process_order to create MRP orders if needed."""
        pos_order_id = super()._process_order(order, draft, existing_order)
        if pos_order_id:
            order = self.browse(pos_order_id)
            order.create_mrp_orders()
        return pos_order_id

    def create_mrp_orders(self):
        """Logic to create MRP orders from POS order lines."""
        for line in self.lines:
            product = line.product_id
            if product.to_create_mrp:
                bom = self.env['mrp.bom']._bom_find(product)[product]
                if bom:
                    mrp_vals = {
                        'product_id': product.id,
                        'product_qty': line.qty,
                        'bom_id': bom.id,
                        'origin': self.name,
                        'company_id': self.company_id.id,
                        'date_start': self.date_order,
                    }
                    mrp_order = self.env['mrp.production'].create(mrp_vals)
                    mrp_order.action_confirm()
                    
                    if product.create_mrp_done:
                        mrp_order.button_mark_done()
