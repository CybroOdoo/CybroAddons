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

from odoo import api, fields, models


class PosOrder(models.Model):
    """
    Inherited model for Point of Sale Orders.
    Adds functionality to automatically create Manufacturing Orders (MRP)
    based on the products sold in the POS interface and links them.
    """
    _inherit = 'pos.order'

    mrp_production_ids = fields.One2many(
        'mrp.production',
        'pos_order_id',
        string="Manufacturing Orders",
        readonly=True,
    )
    mrp_production_count = fields.Integer(
        string="Manufacturing Orders Count",
        compute='_compute_mrp_production_count',
        compute_sudo=True,
    )

    @api.depends('mrp_production_ids')
    def _compute_mrp_production_count(self):
        for order in self:
            order.mrp_production_count = len(order.sudo().mrp_production_ids)

    def action_view_mrp_production(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('mrp.mrp_production_action')
        if self.mrp_production_count == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.mrp_production_ids.id
        else:
            action['domain'] = [('id', 'in', self.mrp_production_ids.ids)]
        return action

    @api.model
    def _process_order(self, order, existing_order):
        """
        Override _process_order to intercept POS order creation and
        generate corresponding MRP orders for configured products once the order is paid.

        :param order: Dictionary containing POS order data from the frontend.
        :param existing_order: Optional existing pos.order record if updating.
        :return: ID of the created or updated pos.order record.
        """
        pos_order_id = super()._process_order(order, existing_order)
        if pos_order_id:
            pos_order = self.browse(pos_order_id)
            if pos_order.state in ['paid', 'done', 'invoiced']:
                pos_order.create_mrp_orders()
        return pos_order_id

    def action_pos_order_paid(self):
        res = super().action_pos_order_paid()
        self.create_mrp_orders()
        return res

    def create_mrp_orders(self):
        """
        Logic to create MRP orders from POS order lines.
        Iterates over the order lines and generates confirmed or done MRP orders
        for products that have 'to_create_mrp' enabled.
        Excludes refund lines (negative qty) and lines that already have an MRP order.
        Uses sudo() to ensure POS cashiers without MRP access rights can process orders.
        """
        for line in self.lines:
            if line.mrp_production_id or line.qty <= 0:
                continue
            product = line.product_id
            if product.to_create_mrp:
                bom = self.env['mrp.bom'].sudo()._bom_find(product)[product]
                if bom:
                    mrp_vals = {
                        'product_id': product.id,
                        'product_qty': line.qty,
                        'bom_id': bom.id,
                        'origin': self.name,
                        'pos_order_id': self.id,
                        'pos_order_line_id': line.id,
                        'company_id': self.company_id.id,
                        'date_start': self.date_order,
                    }
                    mrp_order = self.env['mrp.production'].sudo().create(mrp_vals)
                    line.sudo().write({'mrp_production_id': mrp_order.id})
                    mrp_order.action_confirm()

                    if product.create_mrp_done:
                        mrp_order.button_mark_done()


class PosOrderLine(models.Model):
    """
    Inherited model for Point of Sale Order Lines.
    Links each individual line to its generated Manufacturing Order.
    """
    _inherit = 'pos.order.line'

    mrp_production_id = fields.Many2one(
        'mrp.production',
        string="Manufacturing Order",
        readonly=True,
        copy=False,
    )
