# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class Uom(models.Model):
    """Class inheriting uom model for listing out the products in their
    corresponding unit of measure."""
    _inherit = 'uom.uom'
    _description = 'Product Unit Of Measure'

    products_uom = fields.Integer(compute='compute_product_count',
                                  string="Products",
                                  help="Compute product count in UOM")
    purchase_uom_products = fields.Integer(compute='compute_product_count',
                                           string="Purchase UOM Products",
                                           help="Compute purchase product"
                                                " count in a UOM")

    def action_view_products(self):
        """Smart tab for viewing products with corresponding UOM"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'view_mode': 'kanban,form',
            'res_model': 'product.template',
            'domain': [('uom_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_view_purchase_products(self):
        """Smart tab for viewing products with corresponding Purchase UOM"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'view_mode': 'kanban,form',
            'res_model': 'product.template',
            'domain': [('uom_po_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def compute_product_count(self):
        """Function for computing the count of products with the
        corresponding UOM"""
        for record in self:
            record.products_uom = self.env['product.template'].search_count(
                [('uom_id', '=', record.id)])
            record.purchase_uom_products = self.env[
                'product.template'].search_count(
                [('uom_po_id', '=', record.id)])
