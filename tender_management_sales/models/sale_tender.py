# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
###############################################################################

from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError

SALE_TENDER_STATES = [
    ('draft', 'Draft'),
    ('in_progress', 'Confirmed'),
    ('open', 'Bid Selection'),
    ('done', 'Closed'),
    ('cancel', 'Cancelled')
]


class SaleTenderType(models.Model):
    """Creating a model to store the tender type."""

    _name = "sale.tender.type"
    _description = "Sale Tender Type"

    name = fields.Char(string='Agreement Type', required=True, translate=True,
                       help="Name")
    exclusive = fields.Selection(
        [
            ('exclusive', 'Select only one Quotation (exclusive)'),
            ('multiple', 'Select multiple Quotations (non-exclusive)'),
        ],
        string="Agreement Selection Type",
        required=True,
        default="multiple",
        help=(
            "Exclusive: When a sale order is confirmed, cancel the remaining sale"
            " orders.\n"
            "Non-exclusive: Allows multiple sale orders. Confirming a sale order "
            "does not cancel the remaining ones."
        ),
    )
    quantity_copy = fields.Selection(
        [
            ('copy', 'Use quantities from agreement'),
            ('none', 'Set quantities manually'),
        ],
        string="Quantities",
        required=True,
        default="none",
        help="Choose whether to copy the quantity from the agreement."
    )
    line_copy = fields.Selection(
        [
            ('copy', 'Use lines from agreement'),
            ('none', 'Do not create quotation lines automatically'),
        ],
        string="Lines",
        required=True,
        default="copy",
        help="Choose whether to copy lines from the agreement."
    )


class SaleTender(models.Model):
    """Creating a model to record all the sale tender agreements."""
    _name = "sale.tender"
    _description = "Sale Tender"
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.depends('sale_order_ids')
    def _compute_orders_number(self):
        """Function to compute the number of associated orders for
         the agreement."""
        for tender in self:
            tender.order_count = len(tender.sale_order_ids)

    def action_in_progress(self):
        """Function to activate the current agreement."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("You cannot confirm agreement '%s' because there "
                              "is no product line.", self.name))
        for tender_line in self.line_ids:
            if tender_line.price_unit <= 0.0:
                raise UserError(_('You cannot confirm the Tender without price.'))
            if tender_line.product_qty <= 0.0:
                raise UserError(_('You cannot confirm the Tender order without '
                                  'quantity.'))
        self.write({'state': 'in_progress'})
        if self.name == 'New':
            self.name = self.env['ir.sequence'].next_by_code('sale.tender.order')

    def action_open(self):
        """Function for update current agreement"""
        self.write({'state': 'open'})

    def action_cancel(self):
        """Function to cancel the current agreement."""
        self.write({'state': 'cancel'})

    def action_reset_to_draft(self):
        """Function to reset to draft"""
        self.write({'state': 'draft'})

    def action_done(self):
        """Close the sale tender after ensuring all sale orders are validated or canceled."""
        if any(order.state in ['draft', 'sent']
               for order in self.sale_order_ids):
            raise UserError(
                _('All sale orders must be either confirmed or canceled before closing the sale tender.')
            )
        self.state = 'done'

    name = fields.Char(
        'Reference', required=True, copy=False, default='New', readonly=True,
        help="Name"
    )

    order_count = fields.Integer(
        compute='_compute_orders_number', string='Number of Orders',
        help="Count of orders."
    )

    customer_id = fields.Many2one(
        'res.partner', string="Customer", help="Partner Name",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )

    type_id = fields.Many2one(
        'sale.tender.type', string="Agreement Type", required=True,
        help="Type of the Agreement."
    )

    ordering_date = fields.Date(
        string="Ordering Date", tracking=True,
        help="Date of order."
    )

    date_end = fields.Datetime(
        string='Agreement Deadline', tracking=True,
        help="The Deadline given for the agreement."
    )

    schedule_date = fields.Date(
        string='Delivery Date', index=True, tracking=True,
        help="The expected and scheduled delivery date where all the products are received"
    )

    user_id = fields.Many2one(
        'res.users', string='Sales Representative',
        help="Sales Representative", default=lambda self: self.env.user,
        check_company=True
    )

    description = fields.Html(help="Description")

    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company, help="Company"
    )

    sale_order_ids = fields.One2many(
        'sale.order', 'tender_id', string='Sale Orders',
        help="Log the number of orders using the Agreement",
        states={'done': [('readonly', True)]}
    )

    line_ids = fields.One2many(
        'sale.tender.line', 'tender_id', string='Products to Sell',
        help="Tender Lines", states={'done': [('readonly', True)]},
        copy=True
    )

    state = fields.Selection(
        SALE_TENDER_STATES, 'Status', tracking=True, required=True,
        copy=False, default='draft', help="Track the state of the record"
    )

    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True,
        default=lambda self: self.env.company.currency_id.id,
        help="Currency used."
    )

    exclusive = fields.Selection(related='type_id.exclusive', string='Exclusive', store=False, help="Tender Type")


class SaleTender_idLine(models.Model):
    """Creating the model to store the lines in the tender."""
    _name = "sale.tender.line"
    _inherit = 'analytic.mixin'
    _description = "Sale Tender Line"
    _rec_name = 'product_id'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Function to update the line price."""
        self.price_unit = self.product_id.list_price
        self.product_qty = 1

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update UoM and enforce restrictions."""
        for vals in vals_list:
            if not vals.get('product_uom_id'):
                product = self.env["product.product"].browse(vals.get('product_id'))
                vals['product_uom_id'] = product.uom_id.id

        lines = super().create(vals_list)

        for line, vals in zip(lines, vals_list):
            if (line.tender_id.state not in ['draft', 'cancel', 'done'] and
                    line.tender_id.type_id.quantity_copy == 'none' and
                    vals['price_unit'] <= 0.0):
                raise UserError(_('You cannot confirm the blanket order without a price.'))

        return lines

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        domain=[('sale_ok', '=', True)],
        required=True,
        help="Name of product"
    )

    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Product Unit of Measure',
        domain="[('category_id', '=', product_uom_category_id)]",
        help="Product Unit of Measure"
    )

    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id',
        help="Product Unit of Measure Category"
    )

    product_qty = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        help="Product Quantity"
    )

    product_description_variants = fields.Char(
        'Custom Description',
        help="Product Description"
    )

    price_unit = fields.Float(
        string='Unit Price',
        digits='Product Price',
        help="Product Unit Price"
    )

    tender_id = fields.Many2one(
        'sale.tender',
        required=True,
        string='Sale Agreement',
        ondelete='cascade',
        help="Sale Agreement Select"
    )

    company_id = fields.Many2one(
        'res.company',
        related='tender_id.company_id',
        string='Company',
        store=True,
        readonly=True,
        help="Company"
    )

    schedule_date = fields.Date(
        string='Scheduled Date',
        help="To Add Schedule Date"
    )

    def _prepare_sale_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        """Prepare sale order line values."""
        self.ensure_one()

        if self.product_description_variants:
            name = f"{name}\n{self.product_description_variants}"

        return {
            'name': name,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': product_qty,
            'price_unit': price_unit,
            'tax_id': [Command.set(taxes_ids or [])],
            'analytic_distribution': self.analytic_distribution,
        }
