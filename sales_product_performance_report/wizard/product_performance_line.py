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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Report lines of the product performance report."""
from odoo import fields, models
from odoo.exceptions import UserError


class ProductPerformanceLine(models.TransientModel):
    """One report row, owned by one wizard run (and so by one user)."""

    _name = 'product.performance.line'
    _description = "Product Performance Line"
    _order = 'product_tmpl_id, company_id'

    wizard_id = fields.Many2one(
        comodel_name='product.performance',
        required=True,
        index=True,
        ondelete='cascade',
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        readonly=True,
        ondelete='cascade',
    )
    categ_id = fields.Many2one(
        related='product_tmpl_id.categ_id',
        string='Product Category',
        store=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        readonly=True,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        readonly=True,
        help='Warehouse holding most of the stock of the product',
    )
    quantity = fields.Float(
        string='On Hand',
        readonly=True,
        help='Current On Hand Quantity',
    )
    revenue = fields.Monetary(
        currency_field='currency_id',
        readonly=True,
        help='Total revenue of the confirmed sales orders',
    )
    total_order = fields.Integer(
        readonly=True,
        help='Number of confirmed sales orders containing the product',
    )
    ordered_quantities = fields.Float(
        readonly=True,
        help='Total Ordered Quantities',
    )
    delivered_quantities = fields.Float(
        readonly=True,
        help='Total Delivered Quantities, net of the returns',
    )
    returned_quantities = fields.Float(
        readonly=True,
        help='Total Returned Quantities',
    )
    avg_price = fields.Monetary(
        currency_field='currency_id',
        readonly=True,
        help='Average unit price of the product on the sales order lines',
    )
    avg_ordered_qty = fields.Float(
        string="Avg Ordered Qty Per Order",
        readonly=True,
        help='Average Ordered Quantity Per Order',
    )
    avg_delivered_qty = fields.Float(
        string="Avg Delivered Qty Per Order",
        readonly=True,
        help='Average Delivered Quantity Per Order',
    )

    def action_sale_order(self):
        """Open the sale orders behind this line.

        :return: action opening sale order list and form views
        :raises UserError: when the user can see no order for the line
        """
        self.ensure_one()
        wizard = self.wizard_id
        companies = self.company_id or wizard._get_scope_companies()
        domain = wizard._get_sale_line_domain(self.product_tmpl_id, companies)
        orders = self.env['sale.order.line'].search(domain).order_id
        if not orders:
            raise UserError(self.env._("No Orders with this Product!"))
        return {
            'name': self.env._('Product Performance Report'),
            'res_model': 'sale.order',
            'views': [(False, 'list'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', orders.ids)],
        }
