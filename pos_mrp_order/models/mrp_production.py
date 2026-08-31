# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>
#    Author: AYANA KP (odoo@cybrosys.com)
#
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """ Extends MRP Production model for creating manufacturing orders from POS
    orders."""
    _inherit = 'mrp.production'

    @api.model
    def create_mrp_from_pos(self, product_list):
        """Create MRP Production orders from POS product data."""
        if not product_list:
            raise UserError(_("No products provided."))
        valid_products = [
            p for p in product_list
            if p.get("id") and p.get("qty", 0) > 0
        ]
        if not valid_products:
            raise UserError(_("No valid products found."))
        product_ids = [p["id"] for p in valid_products]
        products = self.env["product.product"].browse(product_ids).exists()
        bom_data = self.env["mrp.bom"]._bom_find(products)
        created_orders = []
        for pdata in valid_products:
            product = products.filtered(lambda p: p.id == pdata["id"])
            bom = bom_data.get(product)
            if not product or not bom:
                continue
            mrp_order = self.create({
                "product_id": product.id,
                "product_qty": pdata["qty"],
                "product_uom_id": product.uom_id.id,
                "origin": f"POS-{pdata['pos_reference']}",
                "bom_id": bom.id,
            })
            moves = [(0, 0, {
                "raw_material_production_id": mrp_order.id,
                "product_id": line.product_id.id,
                "product_uom": line.product_uom_id.id,
                "product_uom_qty": line.product_qty * pdata["qty"],
                "picking_type_id": mrp_order.picking_type_id.id,
                "location_id": mrp_order.location_src_id.id,
                "location_dest_id": line.product_id.with_company(
                    mrp_order.company_id.id).property_stock_production.id,
                "company_id": mrp_order.company_id.id,
            }) for line in bom.bom_line_ids]
            mrp_order.write({"move_raw_ids": [(5, 0, 0)] + moves})
            mrp_order.action_confirm()
            created_orders.append(mrp_order)
