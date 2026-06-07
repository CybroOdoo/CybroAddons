# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CreateBulkOrder(models.Model):
    """Model to manage Bulk Orders.

    A Bulk Order groups multiple order lines that can be used to create:
      - Sale Orders
      - Purchase Orders
      - Manufacturing Orders

    It maintains relationships to the generated documents and provides
    smart-tab actions to view linked orders.
    """
    _name = 'create.bulk.order'
    _description = 'Create Bulk Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Name', readonly=True, default='New', copy=False, tracking=True,
        help="Unique identifier for the bulk order generated using a sequence."
    )
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        help="Customer or vendor associated with the bulk order."
    )
    date = fields.Datetime(
        string='Date', default=fields.Datetime.now, tracking=True,
        help="Date when the bulk order is created."
    )
    bulk_order_line_ids = fields.One2many(
        'bulk.order.line', 'order_id',
        string='Bulk Order Lines', required=True,
        help="List of order lines included in the bulk order."
    )
    order_type = fields.Selection(
        [('sale', 'Sale Order'), ('purchase', 'Purchase Order'),
         ('manufacturing', 'Manufacturing Order')],
        string='Order Type', default='sale',
        help="Specifies which type of order will be created from this bulk order."
    )
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'),
         ('order_confirm', 'Order Created'), ('done', 'Done'),
         ('cancel', 'Cancel')],
        string='State', default='draft', tracking=True,
        help="Current status of the bulk order."
    )
    sale_order_ids = fields.One2many(
        'sale.order', 'bulk_order_id',
        string='Sale Orders',
        help="Sale Orders created from this bulk order."
    )
    purchase_order_ids = fields.One2many(
        'purchase.order', 'bulk_order_id',
        string='Purchase Orders',
        help="Purchase Orders created from this bulk order."
    )
    manufacturing_order_ids = fields.One2many(
        'mrp.production', 'bulk_order_id',
        string='Manufacturing Orders',
        help="Manufacturing Orders generated from this bulk order."
    )
    sale_order_count = fields.Integer(
        string='Sale Order Count', compute='_compute_sale_order_count',
        help="Total number of sale orders linked to this bulk order."
    )
    purchase_order_count = fields.Integer(
        string='Purchase Order Count', compute='_compute_purchase_order_count',
        help="Total number of purchase orders linked to this bulk order."
    )
    manufacturing_order_count = fields.Integer(
        string='Manufacturing Order Count',
        compute='_compute_manufacturing_order_count',
        help="Total number of manufacturing orders linked to this bulk order."
    )

    def action_confirm(self):
        """Confirm the bulk order.

        - Assigns a unique sequence number based on order type.
        - Ensures at least one order line exists.
        - Moves the bulk order to the 'confirm' state.
        """
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
        """Generate a Sale Order based on bulk order lines.

        - Validates customer selection.
        - Creates sale order lines using product, quantity, and price.
        - Links the generated sale order to the bulk order.
        """
        for rec in self:
            if not rec.partner_id:
                raise UserError(_('Please select a customer.'))

            order_lines = [(0, 0, {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty,
                'price_unit': line.list_price,
            }) for line in rec.bulk_order_line_ids]

            self.env['sale.order'].create({
                'partner_id': rec.partner_id.id,
                'order_line': order_lines,
                'bulk_order_id': rec.id,
            })
            rec.state = 'done'

    def action_create_purchase_order(self):
        """Generate a Purchase Order based on bulk order lines.

        - Validates vendor selection.
        - Uses product cost for pricing.
        - Links the created purchase order to the bulk order.
        """
        for rec in self:
            if not rec.partner_id:
                raise UserError(_('Please select a vendor.'))

            order_lines = [(0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.qty,
                'name': line.product_id.name,
                'price_unit': line.product_cost,
            }) for line in rec.bulk_order_line_ids]

            self.env['purchase.order'].create({
                'partner_id': rec.partner_id.id,
                'order_line': order_lines,
                'bulk_order_id': rec.id,
            })
            rec.state = 'done'

    def action_create_manufacturing_order(self):
        """Generate Manufacturing Orders from bulk order lines.

        - Ensures BOM exists for each product.
        - Creates manufacturing orders with BOM, quantity and product info.
        - Links them to the bulk order.
        """
        for rec in self:
            for line in rec.bulk_order_line_ids:
                if not line.bom_id:
                    raise ValidationError(
                        _(f"There are no BOM for the product "
                          f"{line.product_id.name}. Please create one to "
                          f"generate Manufacturing Orders."))
                self.env['mrp.production'].create({
                    'product_id': line.product_id.id,
                    'product_qty': line.qty,
                    'bom_id': line.bom_id.id,
                    'product_uom_id': line.product_id.uom_id.id,
                    'bulk_order_id': rec.id,
                })
            rec.state = 'done'

    def action_reset_to_draft(self):
        """Reset the bulk order to the draft state."""
        for rec in self:
            rec.state = 'draft'

    def _compute_sale_order_count(self):
        """Compute the total number of sale orders linked to the bulk order."""
        for rec in self:
            rec.sale_order_count = len(rec.sale_order_ids)

    def _compute_purchase_order_count(self):
        """Compute the total number of purchase orders linked to the bulk order."""
        for rec in self:
            rec.purchase_order_count = len(rec.purchase_order_ids)

    def _compute_manufacturing_order_count(self):
        """Compute the total number of manufacturing orders linked to the bulk order."""
        for rec in self:
            rec.manufacturing_order_count = len(rec.manufacturing_order_ids)

    def get_sale_order(self):
        """Open an action window showing Sale Orders linked to this bulk order.

        Removes default filters from the sale order action to ensure that
        domain results are shown correctly.
        """
        self.ensure_one()
        action = self.env.ref('sale.action_orders').read()[0]

        action['context'] = {'search_default_filter': 0}

        action['domain'] = [('bulk_order_id', '=', self.id)]
        return action

    def get_purchase_order(self):
        """Open an action window showing Purchase Orders linked to this bulk order."""
        self.ensure_one()
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [('bulk_order_id', '=', self.id)]
        return action

    def get_manufacturing_order(self):
        """Open an action window showing Manufacturing Orders linked to this bulk order."""
        self.ensure_one()
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = [('bulk_order_id', '=', self.id)]
        return action


class BulkOrderLine(models.Model):
    """Order line model representing a product entry inside a Bulk Order."""
    _name = 'bulk.order.line'
    _description = 'Create Bulk Order Line'

    name = fields.Char(
        string='Name', help="Name or description of the order line."
    )
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        help="Product associated with this order line."
    )
    qty = fields.Float(
        string='Quantity', default=1, required=True,
        help="Quantity of the product to be used in the order."
    )
    order_id = fields.Many2one(
        'create.bulk.order', string='Order',
        help="Reference to the parent bulk order."
    )
    list_price = fields.Float(
        string='Price', help="Unit sale price of the product."
    )
    product_cost = fields.Float(
        string='Cost', help="Unit purchase/manufacturing cost of the product."
    )
    bom_id = fields.Many2one(
        'mrp.bom', string="Bill of Material",
        domain="[('product_id', '=', product_id)]",
        help="The Bill of Materials used for manufacturing this product."
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update price and cost fields when product is changed."""
        if self.product_id:
            self.list_price = self.product_id.list_price
            self.product_cost = self.product_id.standard_price
        else:
            self.list_price = 0
            self.product_cost = 0

    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        """Automatically update the product based on selected BOM."""
        if self.bom_id:
            self.product_id = self.bom_id.product_tmpl_id.product_variant_id.id
        else:
            self.product_id = False
