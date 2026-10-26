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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    """Inherited Product to add order partner id and price history actions."""
    _inherit = "product.product"

    order_partner_id = fields.Many2one(
        'res.partner',
        string="Partner",
        compute='_compute_order_partner_id',
        store=False,
        help='Order Partner',
    )

    @api.depends_context('default_order_partner_id', 'order_partner_id')
    def _compute_order_partner_id(self):
        """Compute the order partner from the execution context."""
        partner_id = (
            self.env.context.get('default_order_partner_id')
            or self.env.context.get('order_partner_id')
        )
        for product in self:
            product.order_partner_id = partner_id or False

    def action_sale_product_prices(self):
        """On clicking this button sales details such as partner and price could
         be viewed """
        self.ensure_one()
        rel_view_id = self.env.ref(
            'sale_purchase_previous_product_cost.sale_order_line_view_list')
        domain = [('product_id', '=', self.id)]
        partner_id = (
            self.order_partner_id.id
            or self.env.context.get('default_order_partner_id')
            or self.env.context.get('order_partner_id')
        )
        if partner_id:
            domain.append(('order_partner_id', '=', partner_id))
        sale_lines = self.env['sale.order.line'].search(
            domain, order='create_date DESC').ids
        if not sale_lines:
            raise UserError(_("No sales history found!"))
        ctx = dict(self.env.context)
        if partner_id:
            ctx['default_order_partner_id'] = partner_id
        return {
            'domain': [('id', 'in', sale_lines)],
            'views': [(rel_view_id.id, 'list')],
            'name': _('Sales History'),
            'res_model': 'sale.order.line',
            'view_mode': 'list',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }

    def action_purchase_product_prices(self):
        """On clicking this button Purchase details such as partner and price
        could be viewed """
        self.ensure_one()
        rel_view_id = self.env.ref(
            'sale_purchase_previous_product_cost.purchase_order_line_view_list')
        domain = [('product_id', '=', self.id)]
        partner_id = (
            self.order_partner_id.id
            or self.env.context.get('default_order_partner_id')
            or self.env.context.get('order_partner_id')
        )
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        purchase_lines = self.env['purchase.order.line'].search(
            domain, order='create_date DESC').ids
        if not purchase_lines:
            raise UserError(_("No purchase history found!"))
        ctx = dict(self.env.context)
        if partner_id:
            ctx['default_order_partner_id'] = partner_id
        return {
            'domain': [('id', 'in', purchase_lines)],
            'views': [(rel_view_id.id, 'list')],
            'name': _('Purchase History'),
            'res_model': 'purchase.order.line',
            'view_mode': 'list',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }
