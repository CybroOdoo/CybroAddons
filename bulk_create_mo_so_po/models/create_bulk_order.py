# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu P(odoo@cybrosys.com)
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
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class CreateBulkOrder(models.Model):
    """Creates the model create.bulk.order"""
    _name = 'create.bulk.order'
    _description = 'Create Bulk Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', readonly=True, default='New', copy=False,
                       tracking=True, help="Name of the bulk order")
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help="Customer of the bulk order")
    date = fields.Datetime(string='Date', default=fields.Datetime.now,
                           tracking=True, help="Date of the bulk order")
    bulk_order_line_ids = fields.One2many('bulk.order.line', 'order_id',
                                          string='Bulk Order Lines',
                                          required=True, tracking=True,
                                          help="Bulk orders in the bulk order")
    order_type = fields.Selection(
        [('sale', 'Sale Order'), ('purchase', 'Purchase Order'),
         ('manufacturing', 'Manufacturing Order')], string='Order Type',
        default='sale', help="Order Type of the order")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('order_confirm', 'Order Created'),
                              ('done', 'Done'), ('cancel', 'Cancel')],
                             string='State', default='draft', tracking=True,
                             help="State of the Bulk Order")
    sale_order_ids = fields.One2many('sale.order', 'bulk_order_id',
                                     string='Sale Orders',
                                     help="Sale Orders linked to this bulk "
                                          "order")
    purchase_order_ids = fields.One2many('purchase.order', 'bulk_order_id',
                                         string='Purchase Orders',
                                         help="Purchase Orders linked to this "
                                              "bulk order")
    manufacturing_order_ids = fields.One2many('mrp.production', 'bulk_order_id',
                                              string='Manufacturing Orders',
                                              help="Manufacturing Orders linked"
                                                   " to this bulk order")
    sale_order_count = fields.Integer(string='Sale Order Count',
                                      compute='_compute_sale_order_count',
                                      help="Count of the sale order linked to "
                                           "this bulk order")
    purchase_order_count = fields.Integer(string='Purchase Order Count',
                                          compute='_compute_purchase_order_count',
                                          help="Count of the purchase order "
                                               "linked to this bulk order")
    manufacturing_order_count = fields.Integer(
        string='Manufacturing Order Count',
        compute='_compute_manufacturing_order_count',
        help="Count of the manufacturing order linked to this bulk order")

    def action_confirm(self):
        """Method action_confirm to confirm the bulk order"""
        for rec in self:
            if not rec.name or rec.name == 'New':
                if rec.order_type == 'sale':
                    rec.name = self.env['ir.sequence'].next_by_code(
                        'create.bulk.so.order')
                elif rec.order_type == 'purchase':
                    rec.name = self.env['ir.sequence'].next_by_code(
                        'create.bulk.po.order')
                elif rec.order_type == 'manufacturing':
                    rec.name = self.env['ir.sequence'].next_by_code(
                        'create.bulk.mo.order')
            if not rec.bulk_order_line_ids:
                raise UserError(_('Please add at least one product.'))
            rec.state = 'confirm'

    def action_create_sale_order(self):
        """Method action_create_sale_order to create sale order from the bulk
        order"""
        for rec in self:
            if not rec.partner_id:
                raise UserError(_('Please select a customer.'))
            order_line = []
            for line in rec.bulk_order_line_ids:
                order_line.append((0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                }))
            self.env['sale.order'].create({
                'partner_id': rec.partner_id.id,
                'order_line': order_line,
                'bulk_order_id': rec.id,
            })
            rec.state = 'done'

    def action_create_purchase_order(self):
        """Method action_create_purchase_order to create the purchase order
        from the bulk order"""
        for rec in self:
            if not rec.partner_id:
                raise UserError(_('Please select a vendor.'))
            order_line = []
            for line in rec.bulk_order_line_ids:
                order_line.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.qty,
                    'name': line.product_id.name,
                }))
            self.env['purchase.order'].create({
                'partner_id': rec.partner_id.id,
                'order_line': order_line,
                'bulk_order_id': rec.id,
            })
            rec.state = 'done'

    def action_create_manufacturing_order(self):
        """Method action_create_manufacturing_order to create the
        manufacturing order from the bulk order"""
        for rec in self:
            for line in rec.bulk_order_line_ids:
                if not line.bom_id:
                    raise ValidationError(
                        _(f"There are no BOM for the product "
                          f"variant {line.product_id.name}, please create one "
                          f"BOM to create Manufacturing Order."))
                self.env['mrp.production'].create({
                    'product_id': line.product_id.id,
                    'product_qty': line.qty,
                    'bom_id': line.bom_id.id,
                    'product_uom_id': line.product_id.uom_id.id,
                    'bulk_order_id': rec.id,
                })
            rec.state = 'done'

    def action_reset_to_draft(self):
        """Method action_reset_to_draft to reset the bulk order into draft
        state"""
        for rec in self:
            rec.state = 'draft'

    def _compute_sale_order_count(self):
        """Method _compute_sale_order_count to compute the sale order count"""
        for rec in self:
            rec.sale_order_count = len(rec.sale_order_ids)

    def _compute_purchase_order_count(self):
        """Method _compute_purchase_order_count to compute the purchase order
        count"""
        for rec in self:
            rec.purchase_order_count = len(rec.purchase_order_ids)

    def _compute_manufacturing_order_count(self):
        """Method _compute_manufacturing_order_count to compute the
        manufacturing order counts"""
        for rec in self:
            rec.manufacturing_order_count = len(rec.manufacturing_order_ids)

    def get_sale_order(self):
        """Method get_sale_order to get the sale orders linked to the bulk
        order"""
        for rec in self:
            action = self.env.ref('sale.action_orders').read()[0]
            action['domain'] = [('bulk_order_id', '=', rec.id)]
            return action

    def get_purchase_order(self):
        """Method get_purchase_order to get the purchase orders linked to the
        bulk order"""
        for rec in self:
            action = self.env.ref('purchase.purchase_rfq').read()[0]
            action['domain'] = [('bulk_order_id', '=', rec.id)]
            return action

    def get_manufacturing_order(self):
        """Method get_manufacturing_order to get the manufacturing orders
        linked to the bulk order"""
        for rec in self:
            action = self.env.ref('mrp.mrp_production_action').read()[0]
            action['domain'] = [('bulk_order_id', '=', rec.id)]
            return action


class BulkOrderLine(models.Model):
    """Creates the model bulk.order.line"""
    _name = 'bulk.order.line'

    name = fields.Char(string='Name', help="Name of the order line")
    product_id = fields.Many2one('product.product', string='Product',
                                 required=True,
                                 help="Product in the order line")
    qty = fields.Float(string='Quantity', required=True,
                       help="Quantity of the product", default=1)
    order_id = fields.Many2one('create.bulk.order', string='Order',
                               help="Bulk order")
    list_price = fields.Float(string='Price', help="Price of the product",
                              related="product_id.lst_price")
    product_cost = fields.Float(string='Cost', help="Cost of the product",
                                related="product_id.standard_price")
    bom_id = fields.Many2one('mrp.bom', string="Bill of Material",
                             help="Bill of Material for this product",
                             domain="[('product_id', '=', product_id)]")


class SaleOrder(models.Model):
    """Inherits the model sale.order to add the field bulk_order_id"""
    _inherit = 'sale.order'

    bulk_order_id = fields.Many2one('create.bulk.order', string='Bulk Order',
                                    help="Bulk order linked to this sale order")


class PurchaseOrder(models.Model):
    """Inherits the model purchase.order to add the field bulk_order_id"""
    _inherit = 'purchase.order'

    bulk_order_id = fields.Many2one('create.bulk.order', string='Bulk Order',
                                    help="Bulk order linked to this purchase "
                                         "order")


class ManufacturingOrder(models.Model):
    """Inherits the model mrp.production to add the field bulk_order_id"""
    _inherit = 'mrp.production'

    bulk_order_id = fields.Many2one('create.bulk.order', string='Bulk Order',
                                    help="Bulk order linked to this MRP Order")
