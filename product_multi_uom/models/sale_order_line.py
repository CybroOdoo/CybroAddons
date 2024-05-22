# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (<https://www.cybrosys.com>)
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


class SaleOrderLine(models.Model):
    """Inherits the class sale.order.line for adding the fields for
    secondary uom and the secondary uom Quantity"""
    _inherit = 'sale.order.line'

    secondary_uom_ids = fields.Many2many('uom.uom',
                                         string="Secondary Uom Ids",
                                         help="For fetching all the secondary"
                                              " uom's")
    secondary_product_uom_id = fields.Many2one(
        'uom.uom', string='Secondary UoM',
        compute='_compute_secondary_product_uom', store=True, readonly=False,
        help="Select the Secondary Uom",
        domain="[('id', 'in', secondary_uom_ids)]")
    secondary_product_uom_qty = fields.Float(string='Secondary Quantity',
                                             help="Select the Secondary Uom "
                                                  "Quantity", default=1)
    is_secondary_readonly = fields.Boolean(string="Is Secondary Uom",
                                           help="The field to check whether"
                                                " the selected uom is"
                                                " secondary and if yes then "
                                                "make the field readonly")

    @api.onchange('secondary_product_uom_id', 'secondary_product_uom_qty')
    def _onchange_secondary_product_uom_id(self):
        """Function that update the product_uom_qty as the value in the
         secondary uom quantity"""
        all_uom = []
        if self.product_id.is_need_secondary_uom:
            self.is_secondary_readonly = True
            for uom in self.product_id.secondary_uom_ids:
                all_uom.append(uom.secondary_uom_id.id)
        if self.is_secondary_readonly:
            self.product_uom_readonly = True
            if self.secondary_product_uom_id.id in all_uom:
                primary_uom_ratio = self.env['secondary.uom.line'].search(
                    [('secondary_uom_id', '=', self.secondary_product_uom_id.id),
                     ('product_id', '=', self.product_id.id)]).mapped(
                    'secondary_uom_ratio')
                converted_uom_qty = primary_uom_ratio[
                                        0] * self.secondary_product_uom_qty
                self.product_uom_qty = converted_uom_qty

    @api.depends('product_id')
    def _compute_secondary_product_uom(self):
        """Compute the default secondary uom"""
        for rec in self:
            if (not rec.product_uom or
                    rec.product_id.uom_id.id != rec.secondary_product_uom_id.id):
                rec.secondary_product_uom_id = rec.product_id.uom_id
            all_secondary_uoms = rec.product_id.secondary_uom_ids.mapped(
                'secondary_uom_id')
            if rec.product_id.is_need_secondary_uom and all_secondary_uoms:
                rec.write({
                    'secondary_uom_ids': [(6, 0, all_secondary_uoms.ids)]
                })
