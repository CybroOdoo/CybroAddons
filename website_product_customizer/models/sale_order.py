# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models


class SaleOrder(models.Model):
    """Extends sale.order to track design customization on orders."""
    _inherit = 'sale.order'
    _description = 'Sale Order'

    has_design_products = fields.Boolean(
        string="Has Designed Products",
        compute='_compute_has_design_products',
        help="Automatically set to True if any order line has an attached customer design customization."
    )
    design_customization_count = fields.Integer(
        string="Design Count",
        compute='_compute_design_customization_count',
        help="Number of order lines that have custom designs attached."
    )

    @api.depends('order_line.design_customization_id')
    def _compute_has_design_products(self):
        for order in self:
            order.has_design_products = any(
                line.design_customization_id for line in order.order_line
            )

    @api.depends('order_line.design_customization_id')
    def _compute_design_customization_count(self):
        for order in self:
            order.design_customization_count = len(
                order.order_line.filtered(lambda l: l.design_customization_id)
            )

    def _cart_find_product_line(self, product_id, uom_id, linked_line_id=False,
                               no_variant_attribute_value_ids=None, **kwargs):
        """Exclude lines with a design customization from merge candidates.

        Each customized product should be its own SO line so that the
        customization label and design data are preserved independently.
        """
        candidates = super()._cart_find_product_line(
            product_id, uom_id, linked_line_id=linked_line_id,
            no_variant_attribute_value_ids=no_variant_attribute_value_ids,
            **kwargs,
        )
        # If the caller is adding a designed product, don't merge into an
        # existing designed line — return only non-designed candidates.
        if kwargs.get('force_new_design_line'):
            candidates = candidates.filtered(lambda l: not l.design_customization_id)
        return candidates

    def action_view_designs(self):
        self.ensure_one()
        customization_ids = self.order_line.mapped('design_customization_id').ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Designs',
            'res_model': 'product.design.customization',
            'view_mode': 'list,form',
            'domain': [('id', 'in', customization_ids)],
        }


class SaleOrderLine(models.Model):
    """Extends sale.order.line to link design customizations."""
    _inherit = 'sale.order.line'
    _description = 'Sale Order Line'

    design_customization_id = fields.Many2one(
        'product.design.customization',
        string="Design Customization",
        help="Link to the customer's design customization record. "
             "Contains the full design data (text, images, positions) for this order line."
    )
    is_designed = fields.Boolean(
        string="Is Designed",
        compute='_compute_is_designed',
        store=True,
        help="Indicates whether this order line has an attached custom design."
    )


    @api.depends('design_customization_id')
    def _compute_is_designed(self):
        for line in self:
            line.is_designed = bool(line.design_customization_id)

