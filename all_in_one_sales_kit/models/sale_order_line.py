# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    """Inherits sale.order.line."""
    _inherit = 'sale.order.line'

    sale_date = fields.Datetime(comodel_name='sale.order', string='Sale Date',
                                related='order_id.date_order', store=True,
                                help="Sale order date")
    product_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse', help='Warehouses')
    order_line_image = fields.Binary(string="Image",
                                     related="product_id.image_1920",
                                     help="Product image should be shown or "
                                          "not.")
    contact_email = fields.Char(string="Email",
                                related="order_partner_id.email",
                                help="Email of the customer.")
    contact_phone = fields.Char(string="Phone no.",
                                related="order_partner_id.phone",
                                help="Phone no. of the customer.")
    qty_available = fields.Float(string="On Hand Quantity",
                                 help='Count of On Hand quantity')
    forecast_quantity = fields.Float(string="Forecast Quantity",
                                     help='Count of Forecast quantity')
    discount = fields.Float(string='Discount (%)',
                            digits=(16, 2), default=0.0,
                            help="Discount in percentage.")
    total_discount = fields.Float(string="Total Discount",
                                  default=0.0, store=True,
                                  help="Total Discount.")
    barcode_scan = fields.Char(string='Product Barcode',
                               help="Here you can provide "
                                    "the barcode for the product")

    def action_get_product_form(self):
        """
           This method returns an action that opens a form view for a specific product.
           It sets the order partner ID based on the order's partner ID and constructs an action
           to open the product's form view with the product's details.
           :return: Dictionary representing an action to open the product's form view.
           :rtype: dict
           """
        self.product_id.order_partner_id = self.order_id.partner_id.id
        return {
            'name': self.product_id.name,
            'view_mode': 'form',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.product_id.id
        }

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
             Overwriting the function for adding functionalities of
             multiple warehouses in the sale order line.
             param previous_product_uom_qty(str):
             Uom quantity of previous product
             boolean: Returns True, if the picking created.
        """
        if self._context.get("skip_procurement"):
            return True
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or not line.product_id.type in (
                    'consu', 'product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty,
                             precision_digits=precision) == 0:
                continue
            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(
                    line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update(
                        {'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update(
                        {'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)
            values = line._prepare_procurement_values(group_id=group_id)
            #replacing default warehouse_id into product_warehouse_id in the
            #sale order line and adding it into procurement values.
            if line.product_warehouse_id:
                values['warehouse_id'] = line.product_warehouse_id
            product_qty = line.product_uom_qty - qty
            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(
                product_qty, quant_uom)
            procurements.append(self.env['procurement.group'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.order_id.partner_shipping_id.property_stock_customer,
                line.product_id.display_name, line.order_id.name,
                line.order_id.company_id, values))
        if procurements:
            self.env['procurement.group'].run(procurements)
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(
                lambda p: p.state not in ['cancel', 'done'])
            if pickings_to_confirm:
                pickings_to_confirm.action_confirm()
        return True

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """it is to check product stock according th the chosen product
        restriction."""
        product_restriction = self.env['ir.config_parameter'].sudo().get_param(
            'sale_stock_restrict.product_restriction')
        check_stock = self.env[
            'ir.config_parameter'].sudo().get_param(
            'sale_stock_restrict.check_stock')
        if product_restriction:
            if check_stock == 'on_hand_quantity':
                self.qty_available = self.product_id.qty_available
            if check_stock == 'forecast_quantity':
                self.forecast_quantity = self.product_id.virtual_available

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        """It is to add the scanned products to the order line."""
        product_rec = self.env['product.product']
        if self.barcode_scan:
            product = product_rec.search([('barcode', '=', self.barcode_scan)])
            self.product_id = product.id

    def action_get_product_history_data(self):
        """It is to pass previous history of the chosen product for that
         customer."""
        values = []
        customer_id = self.order_id.partner_id
        customer_order = self.env['sale.order'].search(
            [('partner_id', '=', customer_id.id), (
                'state', 'in', ('sale', 'done'))])
        for order in customer_order:
            for line in order.order_line:
                if line.product_id == self.product_id:
                    values.append((0, 0, {'sale_order_id': order.id,
                                          'history_price': line.price_unit,
                                          'history_qty': line.product_uom_qty,
                                          'history_total': order.amount_total
                                          }))
        history_id = self.env['product.sale.order.history'].create({
            'product_id': self.product_id.id,
            'product_sale_history_ids': values
        })
        return {
            'name': 'Customer Product Sales History',
            'view_mode': 'form',
            'res_model': 'product.sale.order.history',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': history_id.id
        }

    def action_add_catalog_control(self):
        """It is to add function to the button catalog."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Products'),
            'context': {'order_id': self.env.context.get('id')},
            'res_model': 'product.product',
            'view_mode': 'kanban,tree,form',
            'target': 'current',
        }
