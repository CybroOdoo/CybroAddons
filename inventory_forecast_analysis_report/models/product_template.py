# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Raveena V (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
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
#############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_brand_id = fields.Many2one('product.brand', string="Product Brand",
                                       help="Brand of the Product.")
    supplier_id = fields.Many2one(
        'product.supplierinfo', string="Supplier",
        compute="_compute_suppliers",
        store=True, help="Supplier of the Product.")

    @api.depends('seller_ids.partner_id')
    def _compute_suppliers(self):
        """This function is used to compute the main supplier
        of the product."""
        for rec in self:
            rec.supplier_id = False
            if rec.seller_ids:
                rec.supplier_id = rec.seller_ids[0]
